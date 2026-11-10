#!/usr/bin/env python3
"""Create a draft feature record without overwriting existing project work."""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


class ProjectError(ValueError):
    pass


def unredirected(path):
    """Reject symlink/junction ancestors for paths this tool may create or inspect."""
    absolute = Path(path).expanduser().absolute()
    for item in (absolute, *absolute.parents):
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise ProjectError(f'Redirected path is not supported: {item}')
    if absolute.resolve() != absolute:
        raise ProjectError(f'Use a normalized, non-redirected path: {absolute}')
    return absolute


def checker_module():
    path = Path(__file__).resolve().with_name('spec_check.py')
    spec = importlib.util.spec_from_file_location('feature_record_checker', path)
    module = importlib.util.module_from_spec(spec)
    # Installed skill folders are managed files. A cache created here would
    # survive removal as an unowned file and block a subsequent clean install.
    prior = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior
    return module


def quoted(text):
    # User text remains literal project data and cannot introduce competing ID headings.
    return '\n'.join('> ' + line for line in text.strip().splitlines())


def initialize(root, feature, goal, criterion, mode='autonomous', inputs=None):
    root = unredirected(root)
    if not root.is_dir():
        raise ProjectError('--root must be an existing project directory')
    if not isinstance(feature, str) or len(feature) > 64 or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', feature):
        raise ProjectError('--feature must be a lowercase hyphenated name, starting with a letter, at most 64 characters')
    reserved = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
    if feature in reserved:
        raise ProjectError('Choose a feature name that is not a reserved filesystem name')
    if not isinstance(goal, str) or not goal.strip() or not isinstance(criterion, str) or not criterion.strip():
        raise ProjectError('--goal and --criterion must contain actual nonempty text')
    if mode not in ('guided', 'autonomous'):
        raise ProjectError('--mode must be guided or autonomous')
    if inputs is None:
        inputs = []
    if not isinstance(inputs, list) or any(not isinstance(p, str) or not p.strip() for p in inputs):
        raise ProjectError('--inputs must contain nonempty project-relative paths')
    if len(inputs) != len(set(inputs)):
        raise ProjectError('--inputs must not contain duplicate paths')

    specs = unredirected(root / 'specs')
    destination = unredirected(specs / feature)
    if destination.exists():
        raise ProjectError(f'Feature already exists; resume or revise it instead: {destination}')
    if specs.exists() and not specs.is_dir():
        raise ProjectError('The project specs path is not a directory')
    normalized = []
    for value in inputs:
        relative = Path(value)
        if relative.is_absolute() or '..' in relative.parts:
            raise ProjectError(f'Input must be a contained project-relative path: {value}')
        path = unredirected(root / relative)
        if not path.is_relative_to(root) or not path.exists():
            raise ProjectError(f'Input does not exist inside the project: {value}')
        if destination.is_relative_to(path) or path.is_relative_to(destination):
            raise ProjectError(f'Input contains the feature records; select narrower inputs: {value}')
        normalized.append(path.relative_to(root).as_posix())
    if len(normalized) != len(set(normalized)):
        raise ProjectError('Input paths resolve to the same location')

    prefix = destination.relative_to(root).as_posix()
    data = {
        'schema_version': 2, 'feature': feature, 'mode': mode,
        'stage': 'requirements', 'stop_after': 'requirements',
        'next_action': 'Review the draft requirement and acceptance criterion before design or implementation.',
        'decisions': [], 'blockers': [],
        'artifacts': {'requirements': {'path': f'{prefix}/requirements.md', 'status': 'draft'}},
        'requirements': [{'id': 'R-001', 'status': 'active'}],
        'criteria': [{'id': 'AC-001', 'status': 'active', 'requirements': ['R-001']}],
        'tasks': [], 'inputs': normalized, 'evidence': []
    }
    prose = (f'# {feature.replace("-", " ").title()}\n\n'
             'Draft requirement and acceptance criterion supplied at initialization. Review scope and edge cases before design.\n\n'
             f'### R-001: Requested outcome\n\n{quoted(goal)}\n\n'
             f'### AC-001 (R-001)\n\n{quoted(criterion)}\n')
    made_directories, made_files = [], []
    try:
        if not specs.exists():
            specs.mkdir()
            made_directories.append(specs)
        destination.mkdir()  # Exclusive directory creation prevents competing initializers.
        made_directories.append(destination)
        for name, content in [('requirements.md', prose), ('spec.json', json.dumps(data, indent=2, ensure_ascii=False) + '\n')]:
            path = destination / name
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                made_files.append(path)
                stream.write(content)
        errors, _ = checker_module().validate(root, destination, data)
        if errors:
            raise ProjectError('Draft record validation failed: ' + '; '.join(errors))
    except BaseException:
        # Only exact files/directories created by this invocation are eligible for cleanup.
        for path in reversed(made_files):
            path.unlink(missing_ok=True)
        for path in reversed(made_directories):
            try:
                path.rmdir()  # Never recursively deletes user content added concurrently.
            except OSError:
                pass
        raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    init = commands.add_parser('init', help='Create requirements.md and a schema-version-2 draft record')
    init.add_argument('--root', required=True)
    init.add_argument('--feature', required=True)
    init.add_argument('--goal', required=True)
    init.add_argument('--criterion', required=True)
    init.add_argument('--mode', choices=['guided', 'autonomous'], default='autonomous')
    init.add_argument('--inputs', nargs='+', default=[])
    args = parser.parse_args()
    try:
        destination = initialize(args.root, args.feature, args.goal, args.criterion, args.mode, args.inputs)
        print(json.dumps({'feature': str(destination), 'status': 'draft', 'stage': 'requirements',
                          'stop_after': 'requirements', 'created': ['requirements.md', 'spec.json']}, indent=2))
        return 0
    except (ProjectError, OSError, UnicodeError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
