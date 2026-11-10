#!/usr/bin/env python3
"""Validate spec-suite v2 records and record explicitly requested checks (stdlib only)."""
import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

SCHEMA = Path(__file__).resolve().parents[1] / 'assets' / 'spec.schema.json'

PHASES = ['requirements', 'design', 'plan', 'implement', 'verify', 'complete']
TASK_STATES = ('pending', 'in-progress', 'blocked', 'done', 'superseded')
ARTIFACT_STATES = ('draft', 'ready', 'awaiting-review', 'approved', 'stale')
OUTCOMES = ('pass', 'fail', 'blocked', 'untested')
SKIP_DIRS = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}


class SpecError(ValueError):
    pass


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SpecError(f'Duplicate JSON object key: {key}')
            result[key] = value
        return result

    def nonfinite(value):
        raise SpecError(f'Non-finite JSON number: {value}')

    try:
        return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs,
                          parse_constant=nonfinite)
    except (OSError, ValueError, UnicodeError) as exc:
        raise SpecError(f'Cannot read {path}: {exc}') from exc


def schema_errors(value, schema=None):
    """Evaluate the keywords used by our shipped schema, not arbitrary JSON Schema.

    Supported: $ref to local $defs, type, properties, required, additionalProperties,
    enum/const, pattern, minLength/minItems/minProperties, uniqueItems, items,
    anyOf and date-time format. A full validator may independently use the schema.
    """
    document = read_json(SCHEMA) if schema is None else schema
    errors = []
    types = {'object': lambda x: isinstance(x, dict), 'array': lambda x: isinstance(x, list),
             'string': lambda x: isinstance(x, str), 'integer': lambda x: type(x) is int,
             'null': lambda x: x is None, 'boolean': lambda x: type(x) is bool,
             'number': lambda x: type(x) in (int, float)}

    def walk(item, rule, path, output):
        if '$ref' in rule:
            name = rule['$ref'].removeprefix('#/$defs/')
            walk(item, document['$defs'][name], path, output)
            return
        kind = rule.get('type')
        if kind and not types[kind](item):
            output.append(f'{path}: expected {kind}')
            return
        if 'const' in rule and (type(item) is not type(rule['const']) or item != rule['const']):
            output.append(f'{path}: expected {rule["const"]!r}')
        if 'enum' in rule and item not in rule['enum']:
            output.append(f'{path}: invalid value {item!r}; expected one of {rule["enum"]}')
        if 'anyOf' in rule:
            attempts = []
            for alternative in rule['anyOf']:
                attempt = []
                walk(item, alternative, path, attempt)
                attempts.append(attempt)
            if all(attempts):
                output.append(f'{path}: does not match any permitted shape')
        if isinstance(item, dict):
            for name in rule.get('required', []):
                if name not in item:
                    output.append(f'{path}.{name}: required property missing')
            if len(item) < rule.get('minProperties', 0):
                output.append(f'{path}: object must not be empty')
            for name, child in item.items():
                child_rule = rule.get('properties', {}).get(name)
                if child_rule is None:
                    additional = rule.get('additionalProperties', True)
                    if additional is False:
                        output.append(f'{path}.{name}: unknown property; use extensions for custom metadata')
                    elif isinstance(additional, dict):
                        walk(child, additional, f'{path}.{name}', output)
                else:
                    walk(child, child_rule, f'{path}.{name}', output)
        if isinstance(item, list):
            if len(item) < rule.get('minItems', 0):
                output.append(f'{path}: too few entries')
            if rule.get('uniqueItems'):
                encoded = [json.dumps(child, sort_keys=True) for child in item]
                if len(encoded) != len(set(encoded)):
                    output.append(f'{path}: contains duplicate values')
            if 'items' in rule:
                for index, child in enumerate(item):
                    walk(child, rule['items'], f'{path}[{index}]', output)
        if isinstance(item, str):
            if len(item) < rule.get('minLength', 0):
                output.append(f'{path}: string must not be empty')
            if 'pattern' in rule and re.search(rule['pattern'], item) is None:
                output.append(f'{path}: does not match {rule["pattern"]}')
            if rule.get('format') == 'date-time':
                try:
                    parsed = datetime.fromisoformat(item.replace('Z', '+00:00'))
                    if parsed.tzinfo is None or 'T' not in item:
                        raise ValueError('timezone missing')
                except ValueError:
                    output.append(f'{path}: expected an ISO timestamp with timezone')

    walk(value, document, '$', errors)
    return errors


def within(root, relative):
    if not isinstance(relative, str) or not relative or '\0' in relative or Path(relative).is_absolute():
        raise SpecError(f'Expected a relative path, got {relative!r}')
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise SpecError(f'Path escapes project root: {relative}')
    return path


def writable_child(feature, relative):
    """Resolve the exact write destination and refuse symlinks/reparse redirects."""
    candidate = feature / relative
    # resolve() alone permits an in-root symlink to overwrite unrelated project data.
    if candidate.is_symlink() or candidate.resolve() != candidate.absolute():
        raise SpecError(f'Refusing redirected write path: {candidate}')
    if not candidate.resolve().is_relative_to(feature):
        raise SpecError(f'Write path escapes feature: {candidate}')
    return candidate


@contextmanager
def record_lock(feature):
    lock = writable_child(feature, '.spec-record.lock')
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise SpecError(f'Recording already active, or interrupted lock remains: {lock}. '
                        'Check for active record processes before removing an interrupted lock.') from exc
    try:
        try:
            os.write(descriptor, f'pid={os.getpid()}\n'.encode())
        finally:
            os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def atomic_save(feature, data, expected):
    destination = writable_child(feature, 'spec.json')
    if destination.read_bytes() != expected:
        raise SpecError('spec.json changed during recording; concurrent edits preserved. '
                        'The command log remains; reconcile and rerun recording.')
    temporary = writable_child(feature, '.spec-record.tmp')
    if temporary.exists():
        raise SpecError(f'Interrupted temporary record remains: {temporary}. '
                        'Inspect it before manually removing or recovering it.')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        # The lock serializes this tool; users/external editors must not edit during record.
        if destination.read_bytes() != expected:
            raise SpecError('spec.json changed during recording; concurrent edits preserved')
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def load(feature, root):
    root = Path(root).resolve()
    feature = Path(feature).resolve()
    if not feature.is_relative_to(root):
        raise SpecError('Feature folder must be inside --root')
    data = read_json(feature / 'spec.json')
    if not isinstance(data, dict):
        raise SpecError('spec.json must contain an object')
    return root, feature, data


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root, feature, data):
    """Conservative snapshot of declared files, spec prose and immutable ID/task contracts."""
    files = set()
    inputs = data.get('inputs')
    if not isinstance(inputs, list):
        raise SpecError('inputs must be an array of project-relative files/directories')
    for item in inputs:
        path = within(root, item)
        if not path.exists():
            raise SpecError(f'Missing input: {item}')
        if path == feature or path.is_relative_to(feature):
            raise SpecError('inputs must exclude the feature folder; prose is included automatically')
        candidates = [path] if path.is_file() else path.rglob('*')
        for candidate in candidates:
            relative_parts = candidate.relative_to(root).parts
            if any(part in SKIP_DIRS for part in relative_parts):
                continue
            resolved = candidate.resolve()
            if not resolved.is_relative_to(root):
                raise SpecError(f'Input symlink escapes root: {candidate}')
            if resolved == feature or resolved.is_relative_to(feature):
                raise SpecError('Input directory contains the feature folder; select narrower inputs')
            if candidate.is_file():
                files.add(candidate)
    artifacts = data.get('artifacts', {})
    if not isinstance(artifacts, dict):
        raise SpecError('artifacts must be an object')
    for name in ('requirements', 'design', 'tasks'):
        artifact = artifacts.get(name)
        if artifact:
            if not isinstance(artifact, dict):
                raise SpecError(f'{name} artifact must be an object')
            path = within(root, artifact['path'])
            if not path.is_file():
                raise SpecError(f'Missing artifact: {artifact["path"]}')
            files.add(path)
    if not files:
        raise SpecError('No snapshot files found')
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in sorted(files)}
    semantics = {key: data.get(key) for key in ('schema_version', 'feature', 'requirements', 'criteria', 'design', 'inputs')}
    semantics['task_contracts'] = [
        {key: task.get(key) for key in ('id', 'depends_on', 'requirements', 'criteria', 'done_when')}
        for task in data.get('tasks', []) if isinstance(task, dict)
    ]
    payload = {'files': hashes, 'semantics': semantics}
    signature = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return {'sha256': signature, 'files': hashes}


def validate(root, feature, data, complete=False):
    errors, warnings = [], []
    shape = schema_errors(data)
    if shape:
        return shape, warnings
    if not data['inputs']:
        if complete or data['stage'] == 'complete':
            errors.append('Acceptance requires declared runtime inputs; inputs must not be empty')
        else:
            warnings.append('No runtime inputs declared; valid for prose-only planning, not acceptance')
    if data.get('schema_version') != 2:
        errors.append('schema_version must be 2; migrate legacy records explicitly')
    for key in ('feature', 'next_action'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f'{key} must be a nonempty string')
    if data.get('mode') not in ('guided', 'autonomous'):
        errors.append('mode must be guided or autonomous')
    stage = data.get('stage')
    if stage not in PHASES:
        errors.append(f'stage must be one of {PHASES}')
    if data.get('stop_after') not in PHASES[:-1]:
        errors.append('stop_after must name a stage from requirements through verify')
    if not isinstance(data.get('blockers'), list) or any(not isinstance(b, str) for b in data.get('blockers', [])):
        errors.append('blockers must be an array of strings')
    if not isinstance(data.get('decisions'), list):
        errors.append('decisions must be an array of strings')
    elif any(not isinstance(d, str) for d in data['decisions']):
        errors.append('decisions must be an array of strings')

    collections = {}
    for name, prefix in [('requirements', 'R'), ('criteria', 'AC'), ('tasks', 'T'), ('evidence', 'E')]:
        rows = data.get(name)
        if not isinstance(rows, list):
            errors.append(f'{name} must be an array')
            rows = []
        index = {}
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f'{name} entry must be an object')
                continue
            key = row.get('id')
            if not isinstance(key, str) or not re.fullmatch(prefix + r'-\d{3,}', key):
                errors.append(f'Invalid {name} ID: {key!r}')
                continue
            if key in index:
                errors.append(f'Duplicate ID: {key}')
            index[key] = row
        collections[name] = index
    req, criteria, tasks, evidence = (collections[n] for n in ('requirements', 'criteria', 'tasks', 'evidence'))

    def links(row, field, targets, owner, nonempty=False):
        value = row.get(field)
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            errors.append(f'{owner}.{field} must be an array of IDs')
            return []
        if len(value) != len(set(value)):
            errors.append(f'{owner}.{field} contains duplicate IDs')
        if nonempty and not value:
            errors.append(f'{owner}.{field} must not be empty')
        for key in value:
            if key not in targets:
                errors.append(f'{owner}.{field}: unknown ID {key}')
        return value

    for rows in (req, criteria):
        for key, row in rows.items():
            if row.get('status') not in ('active', 'retired'):
                errors.append(f'{key}.status must be active or retired')
    active_req = {key for key, row in req.items() if row.get('status') == 'active'}
    active_ac = {key for key, row in criteria.items() if row.get('status') == 'active'}
    if not active_req or not active_ac:
        errors.append('At least one active requirement and acceptance criterion is required')
    covered_req = set()
    for key, row in criteria.items():
        refs = links(row, 'requirements', req, key, True)
        if key in active_ac:
            covered_req.update(refs)
            for ref in refs:
                if ref not in active_req:
                    errors.append(f'{key} references retired requirement {ref}')
    for key in active_req - covered_req:
        errors.append(f'{key} has no active acceptance criterion')

    artifacts = data.get('artifacts')
    if not isinstance(artifacts, dict):
        errors.append('artifacts must be an object')
        artifacts = {}
    rank = PHASES.index(stage) if stage in PHASES else 0
    if complete:
        rank = max(rank, PHASES.index('verify'))
    needed = ['requirements'] + (['design'] if rank >= 1 else []) + (['tasks'] if rank >= 2 else [])
    if complete or stage == 'complete':
        needed.append('verification')
    for name in needed:
        if name not in artifacts:
            errors.append(f'Missing artifact record: {name}')
    for name, artifact in artifacts.items():
        if name not in ('requirements', 'design', 'tasks', 'verification') or not isinstance(artifact, dict):
            errors.append(f'Invalid artifact: {name}')
            continue
        if artifact.get('status') not in ARTIFACT_STATES:
            errors.append(f'{name}: invalid artifact status')
        if artifact.get('status') == 'approved' and not artifact.get('approval'):
            errors.append(f'{name}: approved requires a recorded user approval with scope')
        try:
            path = within(root, artifact.get('path'))
            if not path.is_file():
                errors.append(f'Missing artifact file: {path}')
                continue
            if name in ('requirements', 'tasks'):
                text = path.read_text(encoding='utf-8')
                headings = re.findall(r'^#{1,6}\s+((?:R|AC|T)-\d{3,})(?=[:\s]|$)', text, re.M)
                if len(headings) != len(set(headings)):
                    errors.append(f'{name}: duplicate ID headings')
                expected = (active_req | active_ac) if name == 'requirements' else {k for k, v in tasks.items() if v.get('state') != 'superseded'}
                allowed = set(req) | set(criteria) if name == 'requirements' else set(tasks)
                for key in expected - set(headings):
                    errors.append(f'{name}: missing heading for {key}')
                for key in set(headings) - allowed:
                    errors.append(f'{name}: unregistered heading {key}')
        except (SpecError, OSError, UnicodeError) as exc:
            errors.append(str(exc))

    if rank >= 1:
        design = data.get('design')
        if not isinstance(design, dict):
            errors.append('design must contain requirements coverage')
        else:
            coverage = links(design, 'requirements', req, 'design')
            for key in active_req - set(coverage):
                errors.append(f'design does not cover {key}')

    planned_ac = set()
    for key, row in tasks.items():
        state = row.get('state')
        if state not in TASK_STATES:
            errors.append(f'{key}: invalid task state {state!r}; reopen invalidated work as pending or blocked')
        deps = links(row, 'depends_on', tasks, key)
        reqs = links(row, 'requirements', req, key)
        acs = links(row, 'criteria', criteria, key)
        links(row, 'evidence', evidence, key)
        if not isinstance(row.get('done_when'), str) or not row.get('done_when', '').strip():
            errors.append(f'{key}.done_when must describe an observable outcome')
        if state != 'superseded':
            if not reqs and not acs:
                errors.append(f'{key} has no requirement or criterion link')
            planned_ac.update(acs)
            for ref in reqs:
                if ref not in active_req:
                    errors.append(f'{key} references retired requirement {ref}')
            for ref in acs:
                if ref not in active_ac:
                    errors.append(f'{key} references retired criterion {ref}')
        for dep in deps:
            if dep == key:
                errors.append(f'{key} depends on itself')
            if state in ('in-progress', 'done') and dep in tasks and tasks[dep].get('state') != 'done':
                errors.append(f'{key} started/completed before dependency {dep} is done')
    if rank >= 2:
        for key in active_ac - planned_ac:
            errors.append(f'{key} is not covered by any active task')
    # Iterative DFS supports long real plans without Python recursion limits.
    colors = {}
    for key in tasks:
        if colors.get(key) == 'done':
            continue
        colors[key] = 'visiting'
        stack = [(key, iter(tasks[key]['depends_on']))]
        while stack:
            owner, children = stack[-1]
            dep = next(children, None)
            if dep is None:
                colors[owner] = 'done'
                stack.pop()
            elif dep in tasks:
                if colors.get(dep) == 'visiting':
                    errors.append(f'Dependency cycle includes {dep}')
                elif colors.get(dep) != 'done':
                    colors[dep] = 'visiting'
                    stack.append((dep, iter(tasks[dep]['depends_on'])))
    pause = data.get('pause_after_task')
    if pause is not None and (not isinstance(pause, str) or pause not in tasks):
        errors.append('pause_after_task must be null or an existing task ID')
    current = None
    try:
        current = snapshot(root, feature, data)
    except (SpecError, KeyError, TypeError, OSError) as exc:
        errors.append(f'Cannot snapshot inputs: {exc}')
    valid_pass = set()
    for key, row in evidence.items():
        links(row, 'criteria', criteria, key)
        if row.get('outcome') not in OUTCOMES:
            errors.append(f'{key}: invalid evidence outcome')
        if row.get('kind') not in ('command', 'manual'):
            errors.append(f'{key}: kind must be command or manual')
        snap = row.get('snapshot')
        fresh = current is not None and snap == current
        if not fresh:
            warnings.append(f'{key}: outdated evidence; rerun checks after source/spec/input changes')
        if not row.get('recorded_at') or not row.get('context'):
            errors.append(f'{key}: missing recording time or environment context')
        if row.get('kind') == 'command':
            if not isinstance(row.get('command'), list) or not row.get('command'):
                errors.append(f'{key}: missing command arguments')
            elif not row['command'][0].strip():
                errors.append(f'{key}: executable must not be empty')
            try:
                log = within(root, row.get('log'))
                if not log.is_file() or digest(log) != row.get('log_sha256'):
                    errors.append(f'{key}: missing or modified command log')
                    fresh = False
            except (SpecError, OSError) as exc:
                errors.append(f'{key}: {exc}')
                fresh = False
            if row.get('outcome') == 'pass' and row.get('exit_code') != 0:
                errors.append(f'{key}: passing command evidence requires exit_code 0')
                fresh = False
        elif row.get('kind') == 'manual' and not row.get('observation'):
            errors.append(f'{key}: manual evidence requires an actual observation')
            fresh = False
        if row.get('outcome') == 'pass' and fresh:
            valid_pass.add(key)
    for key, row in tasks.items():
        if row.get('state') == 'done':
            ids = row.get('evidence', [])
            # The task's newest referenced attempt wins. Do not cherry-pick an
            # old pass when a newer linked check failed on the same snapshot.
            ordered = [eid for eid in evidence if eid in ids]
            if not ordered or ordered[-1] not in valid_pass:
                errors.append(f'{key} is done without current passing task evidence')
    if complete or stage == 'complete':
        if pause is not None:
            errors.append('Completion requires clearing pause_after_task after explicit continuation authorization')
        if data.get('blockers'):
            errors.append('Completion blocked by recorded blockers')
        for name in needed:
            artifact = artifacts.get(name)
            if not isinstance(artifact, dict) or artifact.get('status') not in ('ready', 'approved'):
                errors.append(f'{name} must be ready or approved for completion')
        for key, row in tasks.items():
            if row.get('state') not in ('done', 'superseded'):
                errors.append(f'{key} is unfinished')
        # Evidence is append-only in recording order. A later failed or outdated
        # attempt must not be hidden by selecting an older green result.
        latest_ac = {}
        for eid, row in evidence.items():
            refs = row.get('criteria', [])
            if isinstance(refs, list):
                for ac in refs:
                    if isinstance(ac, str):
                        latest_ac[ac] = eid
        passed_ac = {ac for ac, eid in latest_ac.items() if eid in valid_pass}
        for key in active_ac - passed_ac:
            errors.append(f'{key} has no current passing acceptance evidence')
    return errors, warnings


def record(root, feature, data, args):
    with record_lock(feature):
        temporary = writable_child(feature, '.spec-record.tmp')
        if temporary.exists():
            raise SpecError(f'Interrupted temporary record remains: {temporary}. '
                            'Inspect it before manually removing or recovering it.')
        if args.manual is not None and not args.manual.strip():
            raise SpecError('Manual evidence must describe an actual nonempty observation')
        # Reload under lock: two commands must not allocate the same evidence ID.
        expected = writable_child(feature, 'spec.json').read_bytes()
        data = read_json(feature / 'spec.json')
        return _record(root, feature, data, args, expected)


def _record(root, feature, data, args, expected):
    # Refuse malformed plans. Existing done/stale evidence gaps may be repaired by a fresh run.
    checking = dict(data)
    if checking.get('stage') == 'complete':
        checking['stage'] = 'verify'
    errors, _ = validate(root, feature, checking)
    fatal = [e for e in errors if 'done without current passing task evidence' not in e]
    if fatal:
        raise SpecError('Repair the record before recording evidence:\n' + '\n'.join(fatal))
    criteria = args.criteria or []
    if len(criteria) != len(set(criteria)):
        raise SpecError('Evidence criteria must not contain duplicate IDs')
    known = {c['id'] for c in data['criteria'] if c['status'] == 'active'}
    if set(criteria) - known:
        raise SpecError('Evidence criteria must name active acceptance criteria')
    before = snapshot(root, feature, data)
    log_dir = writable_child(feature, '.spec-evidence')
    if log_dir.exists() and not log_dir.is_dir():
        raise SpecError(f'Evidence output must be a directory: {log_dir}')
    used = {row['id'] for row in data['evidence']}
    number = max([int(key[2:]) for key in used], default=0) + 1
    while f'E-{number:03}' in used:
        number += 1
    # Do not overwrite an orphaned log retained after a failed atomic save.
    while (log_dir / f'E-{number:03}.log').exists():
        number += 1
    item = {'id': f'E-{number:03}', 'criteria': criteria, 'snapshot': before,
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'context': {'platform': platform.platform(), 'python': sys.version.split()[0]}}
    if args.manual:
        item.update(kind='manual', outcome=args.outcome, observation=args.manual)
        result = 0 if args.outcome == 'pass' else 1
    else:
        command = args.command
        if command and command[0] == '--':
            command = command[1:]
        if not command:
            raise SpecError('Supply -- followed by a command, or --manual with an observed result')
        if not command[0].strip():
            raise SpecError('Executable must not be empty')
        log_dir.mkdir(exist_ok=True)
        log_path = writable_child(feature, f'.spec-evidence/{item["id"]}.log')
        # Logs are retained locally; choose commands that do not print credentials.
        with log_path.open('xb') as log:
            try:
                run = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=args.timeout, shell=False)
                result = run.returncode
                outcome = 'pass' if result == 0 else 'fail'
            except subprocess.TimeoutExpired:
                log.write(b'\nCHECK TIMED OUT\n')
                result, outcome = 124, 'blocked'
            except OSError as exc:
                log.write(str(exc).encode('utf-8'))
                result, outcome = 127, 'blocked'
        item.update(kind='command', command=command, exit_code=result, outcome=outcome,
                    log=log_path.relative_to(root).as_posix(), log_sha256=digest(log_path))
    try:
        unchanged = snapshot(root, feature, data) == before
    except (SpecError, KeyError, TypeError, OSError):
        unchanged = False
    if not unchanged:
        item['outcome'] = 'blocked'
        item['note'] = 'Inputs changed during validation; rerun on stable files'
        result = 1
    data['evidence'].append(item)
    atomic_save(feature, data, expected)
    print(f'{item["id"]}: {item["outcome"]}')
    if item.get('log'):
        print(f'Log: {item["log"]}')
    return 0 if result == 0 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    check = sub.add_parser('check', help='Read-only validation; never executes recorded commands')
    capture = sub.add_parser('record', help='Run an explicit command or record a manual observation')
    for child in (check, capture):
        child.add_argument('feature', help='Feature directory containing spec.json')
        child.add_argument('--root', required=True, help='Project root; all stored paths are relative to it')
    check.add_argument('--complete', action='store_true', help='Also require complete tasks and current acceptance evidence')
    check.add_argument('--json', action='store_true', help='Emit deterministic JSON diagnostics')
    capture.add_argument('--criteria', nargs='*', default=[])
    capture.add_argument('--manual', help='Actual observed behavior; this is an attestation, not an automated test')
    capture.add_argument('--outcome', choices=sorted(OUTCOMES), default='pass')
    capture.add_argument('--timeout', type=float, default=60)
    # Split before parsing, so a misspelled checker option can never become an
    # executable. Only an explicit -- introduces a command.
    argv = sys.argv[1:]
    if '--' in argv:
        delimiter = argv.index('--')
        options, command = argv[:delimiter], argv[delimiter + 1:]
    else:
        options, command = argv, []
    args = parser.parse_args(options)
    if args.action == 'check' and command:
        parser.error('check never executes a command')
    args.command = command
    if args.action == 'record' and (not math.isfinite(args.timeout) or args.timeout <= 0 or args.manual is not None and command):
        parser.error('Use a positive timeout and choose either command or manual evidence')
    try:
        root, feature, data = load(args.feature, args.root)
        if args.action == 'record':
            return record(root, feature, data, args)
        errors, warnings = validate(root, feature, data, args.complete)
        errors, warnings = sorted(set(errors)), sorted(set(warnings))
        if args.json:
            print(json.dumps({'errors': errors, 'warnings': warnings, 'valid': not errors}, sort_keys=True))
        else:
            for warning in warnings:
                print('WARN:', warning)
            for error in errors:
                print('ERROR:', error)
            print(f'{len(errors)} error(s), {len(warnings)} warning(s)')
        return 1 if errors else 0
    except (SpecError, OSError, UnicodeError, RecursionError) as exc:
        if args.action == 'check' and args.json:
            print(json.dumps({'errors': [str(exc)], 'warnings': [], 'valid': False}, sort_keys=True))
        else:
            print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
