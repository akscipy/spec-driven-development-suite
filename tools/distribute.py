#!/usr/bin/env python3
"""Build verified releases and manage local installations (Python 3.10+)."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
# Retained filenames preserve ownership and rollback for existing installations.
INVENTORY = '.codex-spec-suite-install.json'
BACKUPS = '.codex-spec-suite-backups'
LOCK = '.codex-spec-suite.lock'
NAME = 'spec-driven-development-suite'
LEGACY_NAME = 'codex-spec-suite'
SKILLS = {'spec-workflow', 'spec-discover', 'spec-requirements', 'spec-design',
          'spec-plan', 'spec-implement', 'spec-verify', 'spec-review',
          'spec-change', 'spec-resume', 'spec-steering', 'spec-hooks'}
DOCS = {'LICENSE', 'README.md', 'GUIDE.md', 'CHANGELOG.md', 'COMPATIBILITY.md',
        'SECURITY.md', 'CONTRIBUTING.md', 'RELEASE.json', 'VALIDATION.md', 'EVALUATION.md',
        'PRODUCT-BRIEF.md', 'DEMO.md', 'FAQ.md'}
REQUIRED = (DOCS - {'VALIDATION.md', 'EVALUATION.md'}) | {
    'plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json', 'docs/AUDIT.md', 'docs/RELEASE-REPORT.md',
    'skills/spec-workflow/assets/spec.schema.json', 'skills/spec-workflow/references/records.md',
    'skills/spec-workflow/scripts/spec_project.py', 'examples/README.md', 'examples/demo.py',
    'examples/bounded-slug/src/slugs.py', 'examples/bounded-slug/tests/test_slugs.py',
    'examples/bounded-slug/specs/bounded-slug/requirements.md',
    'examples/bounded-slug/specs/bounded-slug/design.md',
    'examples/bounded-slug/specs/bounded-slug/tasks.md',
    'examples/bounded-slug/specs/bounded-slug/spec.json'}
SUFFIXES = {'.md', '.json', '.yaml', '.yml', '.py', '.txt', '.js', '.toml'}


class DistributionError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise DistributionError(f'Cannot read {path}: {exc}') from exc


def canonical(data):
    return (json.dumps(data, sort_keys=True, indent=2) + '\n').encode('utf-8')


def relative(value):
    if not isinstance(value, str) or '\\' in value:
        raise DistributionError(f'Unsafe relative path: {value!r}')
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(p in ('', '.', '..') or ':' in p for p in path.parts):
        raise DistributionError(f'Unsafe relative path: {value!r}')
    return path


def safe(root, value):
    parts = relative(value).parts
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise DistributionError(f'Symlink in managed path: {current}')
        if hasattr(current, 'is_junction') and current.is_junction():
            raise DistributionError(f'Junction in managed path: {current}')
    resolved = current.resolve()
    if not resolved.is_relative_to(root):
        raise DistributionError(f'Path escapes destination: {value}')
    return current


def destination(value):
    raw = Path(value).expanduser().absolute()
    for part in (raw, *raw.parents):
        if part.is_symlink():
            raise DistributionError(f'Symlink in destination path: {part}')
        if hasattr(part, 'is_junction') and part.is_junction():
            raise DistributionError(f'Junction in destination path: {part}')
    resolved = raw.resolve()
    if resolved == Path(resolved.anchor):
        raise DistributionError('A filesystem root is not a skills destination')
    if resolved.exists() and not resolved.is_dir():
        raise DistributionError('Destination must be a directory')
    return resolved


def installation_target(explicit=None, agent=None, scope=None, project=None, home=None, cwd=None):
    """Resolve host discovery locations without editing host configuration."""
    if explicit is not None:
        if any(value is not None for value in (agent, scope, project)):
            raise DistributionError('Use either --destination or --agent/--scope, not both')
        return Path(explicit).expanduser()
    if agent not in ('codex', 'claude') or scope not in ('user', 'project'):
        raise DistributionError('Supply --destination, or both --agent and --scope')
    if project is not None and scope != 'project':
        raise DistributionError('--project is only valid with --scope project')
    base = Path(home) if home is not None else Path.home()
    if scope == 'project':
        base = Path(project) if project is not None else (Path(cwd) if cwd is not None else Path.cwd())
    folder = '.agents' if agent == 'codex' else '.claude'
    return base.expanduser() / folder / 'skills'


def source_files(root=ROOT):
    root = Path(root).resolve()
    metadata = read_json(root / 'RELEASE.json')
    if (not isinstance(metadata, dict) or metadata.get('name') != NAME
            or not isinstance(metadata.get('version'), str)
            or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?', metadata['version'])):
        raise DistributionError('Invalid release identity/version')
    for name in sorted(REQUIRED):
        if not (root / name).is_file():
            raise DistributionError(f'Missing required release resource: {name}')
    paths = []
    for name in sorted(DOCS):
        if (root / name).is_file():
            paths.append(root / name)
    for name in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json',
                 'docs/AUDIT.md', 'docs/RELEASE-REPORT.md', '.github/workflows/ci.yml',
                 'docs/presentation/README.md', 'docs/presentation/Delivery-Overview.pptx',
                 'docs/presentation/Delivery-Overview.pdf', 'docs/presentation/Product-Brief.pdf'):
        if (root / name).is_file():
            paths.append(root / name)
    for folder in ('skills', 'tools', 'tests', 'examples'):
        for p in sorted((root / folder).rglob('*')):
            rel = p.relative_to(root)
            if any(part.startswith('.') or part == '__pycache__' for part in rel.parts):
                continue
            if p.is_file() and p.suffix in SUFFIXES:
                paths.append(p)
    # Benchmark distributions are explicit, avoiding logs and private trial material.
    benchmarks = root / 'benchmarks'
    if benchmarks.exists():
        for p in sorted(benchmarks.rglob('*')):
            rel = p.relative_to(root)
            if p.is_file() and p.suffix in {'.md', '.json', '.py', '.js'} and not any(part.startswith('.') or part == '__pycache__' for part in rel.parts):
                paths.append(p)
    result = {}
    for path in paths:
        rel = path.relative_to(root).as_posix()
        relative(rel)
        safe(root, rel)
        result[rel] = path.read_bytes()
    skills = {p.split('/')[1] for p in result if p.startswith('skills/')}
    if skills != SKILLS:
        raise DistributionError(f'Expected all 12 skill folders; found {sorted(skills)}')
    for name in SKILLS:
        entry = f'skills/{name}/SKILL.md'
        if entry not in result:
            raise DistributionError(f'Missing skill entrypoint: {name}')
        text = result[entry].decode('utf-8')
        if not re.search(rf'^name:\s*[\"\']?{re.escape(name)}[\"\']?\s*$', text, re.M):
            raise DistributionError(f'Skill name does not match its folder: {name}')
        if not re.search(r'^description:\s*\S', text, re.M):
            raise DistributionError(f'Missing skill description: {name}')
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            target = ((root / entry).parent / link.split('#')[0]).resolve()
            if not target.is_relative_to(root) or target.relative_to(root).as_posix() not in result:
                raise DistributionError(f'Unpackaged resource link in {entry}: {link}')
        meta = f'skills/{name}/agents/openai.yaml'
        if meta not in result:
            raise DistributionError(f'Missing skill metadata: {name}')
    for plugin in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
        if plugin in result:
            descriptor = json.loads(result[plugin])
            if (not isinstance(descriptor, dict) or descriptor.get('name') != NAME
                    or descriptor.get('version') != metadata['version']):
                raise DistributionError(f'Plugin identity/version differs from RELEASE.json: {plugin}')
            if plugin != 'plugin.json' and descriptor.get('skills') != './skills/':
                raise DistributionError(f'Plugin must discover the packaged skill directory: {plugin}')
    exported = root / 'MANIFEST.json'
    if exported.exists():
        manifest = read_json(exported)
        actual = {p: sha(content) for p, content in sorted(result.items())}
        if not isinstance(manifest, dict) or manifest.get('name') != NAME or manifest.get('version') != metadata['version'] or manifest.get('files') != actual:
            raise DistributionError('Release manifest mismatch; do not install a modified or incomplete archive')
    return metadata, dict(sorted(result.items()))


def build(output, root=ROOT):
    meta, files = source_files(root)
    manifest = {'name': NAME, 'version': meta['version'], 'files': {p: sha(b) for p, b in files.items()}}
    files['MANIFEST.json'] = canonical(manifest)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'{NAME}-{meta["version"]}.zip'
    temporary = output / f'.{archive.name}.{uuid.uuid4().hex}.tmp'
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for name, content in sorted(files.items()):
                entry = zipfile.ZipInfo(f'{NAME}-{meta["version"]}/{name}', date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = (0o100644 << 16)
                entry.compress_type = zipfile.ZIP_DEFLATED
                package.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary, archive)
    finally:
        temporary.unlink(missing_ok=True)
    checksum = sha(archive.read_bytes())
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    return {'archive': str(archive), 'sha256': checksum, 'files': len(files)}


def owned_path(path):
    parts = relative(path).parts
    if len(parts) < 2 or parts[0] not in SKILLS:
        raise DistributionError(f'Invalid owned skill path: {path}')


def inventory(root, filename=INVENTORY):
    path = safe(root, filename)
    if not path.exists():
        return None
    data = read_json(path)
    if not isinstance(data, dict) or data.get('format') != 1 or data.get('name') not in (NAME, LEGACY_NAME) or not isinstance(data.get('files'), dict):
        raise DistributionError('Unrecognized ownership inventory; refusing mutation')
    for rel, expected in data['files'].items():
        owned_path(rel)
        if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
            raise DistributionError(f'Invalid inventory hash: {rel}')
        safe(root, rel)
    return data


def verify_owned(root, inv):
    changed = []
    if inv:
        for rel, expected in inv['files'].items():
            path = safe(root, rel)
            if not path.is_file() or sha(path.read_bytes()) != expected:
                changed.append(rel)
    if changed:
        raise DistributionError('Locally modified or missing owned files; preserve/reconcile them before updating: ' + ', '.join(changed))


@contextlib.contextmanager
def locked(root):
    root.mkdir(parents=True, exist_ok=True)
    path = safe(root, LOCK)
    try:
        stream = path.open('x', encoding='ascii')
    except FileExistsError as exc:
        raise DistributionError('Another operation holds the installation lock; inspect it before removing a stale lock') from exc
    try:
        with stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)


def atomic(path, data):
    if path.is_file() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f'.{path.name}.{uuid.uuid4().hex}.tmp'
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def create_backup(root, old):
    token = uuid.uuid4().hex
    folder = safe(root, f'{BACKUPS}/{token}')
    folder.mkdir(parents=True)
    old_files = {rel: safe(root, rel).read_bytes() for rel in old['files']} if old else {}
    for rel, content in old_files.items():
        atomic(safe(folder, rel), content)
    atomic(folder / 'inventory.json', canonical(old))
    return token


def apply_files(root, current, desired, record):
    for rel, content in desired.items():
        atomic(safe(root, rel), content)
    for rel in sorted(set(current) - set(desired)):
        safe(root, rel).unlink(missing_ok=True)
    invpath = safe(root, INVENTORY)
    if record is None:
        invpath.unlink(missing_ok=True)
    else:
        atomic(invpath, canonical(record))
    # Do not recurse into directories or delete unowned contents.
    parents = {safe(root, rel).parent for rel in current}
    for parent in sorted(parents, key=lambda p: len(p.parts), reverse=True):
        try:
            parent.rmdir()
        except OSError:
            pass


def install(dest, dry_run=False, root=ROOT):
    meta, source = source_files(root)
    desired = {p[len('skills/'):]: data for p, data in source.items() if p.startswith('skills/')}
    dest = destination(dest)

    def preflight():
        old = inventory(dest)
        verify_owned(dest, old)
        managed = set(old['files']) if old else set()
        old_skills = {p.split('/')[0] for p in managed}
        for skill in SKILLS:
            folder = safe(dest, skill)
            if folder.exists() and skill not in old_skills:
                raise DistributionError(f'Unmanaged skill collision: {skill}; move or back it up explicitly before installation')
        for rel in desired:
            target = safe(dest, rel)
            if target.exists() and rel not in managed:
                raise DistributionError(f'Unmanaged file collision: {rel}')
            if target.exists() and not target.is_file():
                raise DistributionError(f'Target is not a regular file: {rel}')
        return old

    old = preflight()
    result = {'action': 'update' if old else 'install', 'version': meta['version'], 'destination': str(dest), 'files': len(desired), 'dry_run': dry_run}
    if dry_run:
        return result
    with locked(dest):
        old = preflight()
        before = {rel: safe(dest, rel).read_bytes() for rel in old['files']} if old else {}
        backup = create_backup(dest, old)
        record = {'format': 1, 'name': NAME, 'version': meta['version'], 'files': {p: sha(b) for p, b in desired.items()}, 'previous_backup': backup}
        try:
            apply_files(dest, before, desired, record)
            verify_owned(dest, record)
        except BaseException:
            apply_files(dest, desired, before, old)
            raise
        result['backup'] = backup
    return result


def status(dest):
    dest = destination(dest)
    inv = inventory(dest)
    if not inv:
        return {'installed': False, 'destination': str(dest)}
    changed = []
    for rel, expected in inv['files'].items():
        path = safe(dest, rel)
        if not path.is_file() or sha(path.read_bytes()) != expected:
            changed.append(rel)
    return {'installed': True, 'name': inv.get('name'), 'version': inv.get('version'), 'files': len(inv['files']), 'modified': changed, 'destination': str(dest), 'previous_backup': inv.get('previous_backup')}


def uninstall(dest, dry_run=False):
    dest = destination(dest)
    inv = inventory(dest)
    if inv is None:
        raise DistributionError('No managed installation found')
    verify_owned(dest, inv)
    result = {'action': 'uninstall', 'files': len(inv['files']), 'destination': str(dest), 'dry_run': dry_run}
    if dry_run:
        return result
    with locked(dest):
        inv = inventory(dest)
        if inv is None:
            raise DistributionError('Installation changed before uninstall')
        verify_owned(dest, inv)
        backup = create_backup(dest, inv)
        before = {rel: safe(dest, rel).read_bytes() for rel in inv['files']}
        try:
            apply_files(dest, before, {}, None)
        except BaseException:
            apply_files(dest, {}, before, inv)
            raise
        result['backup'] = backup
    return result


def rollback(dest, token=None, dry_run=False):
    dest = destination(dest)

    def preflight():
        inv = inventory(dest)
        verify_owned(dest, inv)
        selected = token or (inv or {}).get('previous_backup')
        if not isinstance(selected, str) or not re.fullmatch('[a-f0-9]{32}', selected):
            raise DistributionError('Supply --backup with a valid retained backup ID')
        folder = safe(dest, f'{BACKUPS}/{selected}')
        old = read_json(safe(folder, 'inventory.json'))
        if old is not None:
            # Reuse inventory validation before trusting backup-owned paths.
            old = inventory(folder, 'inventory.json')
            verify_owned(folder, old)
        before = {rel: safe(dest, rel).read_bytes() for rel in inv['files']} if inv else {}
        desired = {rel: safe(folder, rel).read_bytes() for rel in old['files']} if old else {}
        for rel in desired:
            target = safe(dest, rel)
            if target.exists() and rel not in before:
                raise DistributionError(f'Rollback would overwrite an unmanaged file: {rel}')
        return inv, old, before, desired, selected

    inv, old, before, desired, selected = preflight()
    result = {'action': 'rollback', 'backup': selected, 'version': (old or {}).get('version'), 'destination': str(dest), 'dry_run': dry_run}
    if dry_run:
        return result
    with locked(dest):
        inv, old, before, desired, selected = preflight()
        recovery = create_backup(dest, inv)
        try:
            apply_files(dest, before, desired, old)
        except BaseException:
            apply_files(dest, desired, before, inv)
            raise
        result['recovery_backup'] = recovery
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('validate', help='Check source/package resource integrity without changing files')
    pack = sub.add_parser('build', help='Create a reproducible ZIP and SHA-256 sidecar')
    pack.add_argument('--output', required=True)
    for action in ('install', 'status', 'uninstall', 'rollback'):
        child = sub.add_parser(action)
        child.add_argument('--destination', help='Explicit skill directory; cannot be combined with host/scope options')
        child.add_argument('--agent', choices=('codex', 'claude'), help='Coding assistant whose skill discovery layout to use')
        child.add_argument('--scope', choices=('user', 'project'), help='Personal installation or current/chosen project')
        child.add_argument('--project', help='Project root for project scope; defaults to the current directory')
        if action != 'status':
            child.add_argument('--dry-run', action='store_true')
        if action == 'rollback':
            child.add_argument('--backup', help='Retained backup ID; defaults to the previous installation')
    args = parser.parse_args()
    try:
        target = None
        if args.action in ('install', 'status', 'uninstall', 'rollback'):
            target = installation_target(args.destination, args.agent, args.scope, args.project)
        if args.action == 'validate':
            meta, files = source_files()
            result = {'valid': True, 'version': meta['version'], 'files': len(files)}
        elif args.action == 'build':
            result = build(args.output)
        elif args.action == 'install':
            result = install(target, args.dry_run)
        elif args.action == 'status':
            result = status(target)
        elif args.action == 'uninstall':
            result = uninstall(target, args.dry_run)
        else:
            result = rollback(target, args.backup, args.dry_run)
        print(json.dumps(result, indent=2))
        return 1 if result.get('modified') else 0
    except (DistributionError, OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
