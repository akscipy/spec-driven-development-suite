#!/usr/bin/env python3
"""Copy the bounded-slug example into a new workspace and collect real evidence."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'skills/spec-workflow/scripts/spec_check.py'


def run_demo(workspace):
    workspace = Path(workspace).expanduser().absolute()
    for candidate in (workspace, *workspace.parents):
        if candidate.is_symlink() or (hasattr(candidate, 'is_junction') and candidate.is_junction()):
            raise ValueError(f'Use a workspace without redirected ancestors: {candidate}')
    if workspace.resolve() != workspace or workspace.exists():
        raise ValueError('Choose a normalized workspace path that does not already exist')
    source = ROOT / 'examples/bounded-slug'
    shutil.copytree(source, workspace, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    feature = workspace / 'specs/bounded-slug'
    record_path = feature / 'spec.json'
    data = json.loads(record_path.read_text(encoding='utf-8'))
    data['stage'] = 'implement'
    data['tasks'][0]['state'] = 'in-progress'

    def save():
        record_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

    def command(*arguments):
        run = subprocess.run([sys.executable, '-B', str(CHECKER), *map(str, arguments)],
                             cwd=workspace, capture_output=True, text=True, timeout=90)
        if run.returncode:
            raise RuntimeError(run.stdout + run.stderr)
        return run.stdout.strip()

    save()
    try:
        first = command('record', feature, '--root', workspace, '--criteria',
                        'AC-001', 'AC-002', 'AC-003', '--', sys.executable, '-B', '-m',
                        'unittest', 'discover', '-s', 'tests', '-v')
        data = json.loads(record_path.read_text(encoding='utf-8'))
        test_id = data['evidence'][-1]['id']
        data['tasks'][0].update(state='done', evidence=[test_id])
        data['tasks'][1].update(state='in-progress')
        (feature / 'verification.md').write_text(
            '# Local example verification\n\n'
            f'Command tests were executed and recorded as {test_id}. '
            'The five tests cover normalization, empty input, bounds, and invalid arguments. '
            'Inspect the command output under .spec-evidence for the actual runner result.\n\n'
            'AC-001, AC-002, and AC-003 are linked to that passing test record. '
            'This example has no external services or environment-dependent integration claims.\n',
            encoding='utf-8')
        data['artifacts']['verification'] = {'path': 'specs/bounded-slug/verification.md', 'status': 'ready'}
        data['stage'] = 'verify'
        # The report is now written from actual results. The following real
        # completion check decides whether this local verification task stands.
        data['tasks'][1].update(state='done', evidence=[test_id])
        data['next_action'] = 'Run the final record consistency check and inspect its output'
        save()
        second = command('record', feature, '--root', workspace, '--', sys.executable, '-B',
                         str(CHECKER), 'check', feature, '--root', workspace, '--complete')
        data = json.loads(record_path.read_text(encoding='utf-8'))
        check_id = data['evidence'][-1]['id']
        data['tasks'][1]['evidence'] = [check_id]
        data['stage'] = 'complete'
        data['next_action'] = 'Example complete; inspect logs or change a requirement to observe evidence invalidation'
        save()
        final = command('check', feature, '--root', workspace, '--complete', '--json')
    except BaseException:
        # Preserve the workspace and failed evidence for inspection, but never
        # leave the documentation task claiming completion after a failed check.
        if record_path.is_file():
            data = json.loads(record_path.read_text(encoding='utf-8'))
            if data['tasks'][1]['state'] == 'done':
                data['tasks'][1].update(state='blocked')
                data['blockers'] = ['Final example validation failed; inspect retained output and logs']
                data['stage'] = 'verify'
                save()
        raise
    return {'workspace': str(workspace), 'test_evidence': test_id,
            'record_check_evidence': check_id, 'completion': json.loads(final),
            'commands': [first, second]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, help='New disposable directory; never overwrites an existing path')
    args = parser.parse_args()
    try:
        print(json.dumps(run_demo(args.workspace), indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
