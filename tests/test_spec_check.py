"""Behavioral regression tests for the checker, using isolated temporary projects."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
import sys
import uuid
import unittest
import time
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/spec-workflow/scripts/spec_check.py'
spec = importlib.util.spec_from_file_location('spec_check', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CheckerTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parent / '.runs'
        self.root = (scratch / uuid.uuid4().hex).resolve()
        assert self.root.is_relative_to(scratch)
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.feature = self.root / 'specs/feature'
        self.feature.mkdir(parents=True)
        (self.root / 'src').mkdir()
        (self.root / 'tests').mkdir()
        (self.root / 'src/app.py').write_text('VALUE = 1\n')
        for name, text in {'requirements': '# Feature\n### R-001: Behavior\nObservable behavior\n### AC-001 (R-001)\nVALUE equals 1.\n',
                           'design': '# Design\nUse the existing constant.\n',
                           'tasks': '# Tasks\n## T-001: Implement behavior\nModify src/app.py.\n',
                           'verification': '# Verification\nActual results recorded in spec.json.\n'}.items():
            (self.feature / f'{name}.md').write_text(text)
        self.data = {
            'schema_version': 2, 'feature': 'feature', 'mode': 'autonomous', 'stage': 'plan', 'stop_after': 'verify',
            'next_action': 'Implement T-001', 'decisions': [], 'blockers': [],
            'artifacts': {n: {'path': f'specs/feature/{n}.md', 'status': 'ready'} for n in ('requirements', 'design', 'tasks', 'verification')},
            'requirements': [{'id': 'R-001', 'status': 'active'}],
            'criteria': [{'id': 'AC-001', 'status': 'active', 'requirements': ['R-001']}],
            'design': {'requirements': ['R-001']},
            'tasks': [{'id': 'T-001', 'state': 'pending', 'depends_on': [], 'requirements': ['R-001'], 'criteria': ['AC-001'], 'done_when': 'Expected behavior is demonstrated', 'evidence': []}],
            'inputs': ['src', 'tests'], 'evidence': []}
        self.save()

    def save(self):
        (self.feature / 'spec.json').write_text(json.dumps(self.data), encoding='utf-8')

    def errors(self, complete=False):
        return checker.validate(self.root, self.feature, self.data, complete)[0]

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)

    def record(self, code='assert __import__("src.app", fromlist=["VALUE"]).VALUE == 1'):
        self.save()
        result = self.cli('record', self.feature, '--root', self.root, '--criteria', 'AC-001', '--', sys.executable, '-c', code)
        self.data = json.loads((self.feature / 'spec.json').read_text())
        return result

    def done(self):
        self.data['tasks'][0].update(state='done', evidence=[self.data['evidence'][-1]['id']])

    def test_valid_plan_but_not_complete(self):
        self.assertEqual(self.errors(), [])
        self.assertTrue(any('unfinished' in e for e in self.errors(True)))

    def test_real_check_records_log_and_supports_completion(self):
        result = self.record()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.done()
        self.assertEqual(self.errors(True), [])

    def test_real_failure_is_not_acceptance(self):
        result = self.record('assert False, "intentional failing acceptance check"')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.data['evidence'][0]['outcome'], 'fail')
        self.done()
        self.assertTrue(any('without current passing' in e for e in self.errors(True)))

    def test_source_change_invalidates_done_evidence(self):
        self.record()
        self.done()
        (self.root / 'src/app.py').write_text('VALUE = 2\n')
        self.assertTrue(any('without current passing' in e for e in self.errors()))

    def test_new_file_in_input_directory_invalidates_evidence(self):
        self.record()
        self.done()
        (self.root / 'src/new_dependency.py').write_text('CONFIG = 3\n')
        self.assertTrue(any('without current passing' in e for e in self.errors()))

    def test_spec_prose_change_invalidates_evidence(self):
        self.record()
        self.done()
        with (self.feature / 'requirements.md').open('a') as file:
            file.write('New required behavior.\n')
        self.assertTrue(any('without current passing' in e for e in self.errors()))

    def test_spec_metadata_change_invalidates_evidence(self):
        self.record()
        self.done()
        self.data['requirements'].append({'id': 'R-002', 'status': 'retired'})
        self.assertTrue(any('without current passing' in e for e in self.errors()))

    def test_task_status_change_does_not_invalidate_evidence(self):
        self.record()
        self.done()
        self.data['stage'] = 'verify'
        self.data['next_action'] = 'Review actual evidence'
        self.assertEqual(self.errors(True), [])

    def test_modified_log_is_rejected(self):
        self.record()
        self.done()
        log = self.root / self.data['evidence'][0]['log']
        log.write_text('altered log')
        self.assertTrue(any('modified command log' in e for e in self.errors(True)))

    def test_dependency_cycle_and_premature_start(self):
        task = copy.deepcopy(self.data['tasks'][0])
        task.update(id='T-002', depends_on=['T-001'])
        self.data['tasks'].append(task)
        self.data['tasks'][0].update(depends_on=['T-002'], state='in-progress')
        errors = self.errors()
        self.assertTrue(any('cycle' in e for e in errors))
        self.assertTrue(any('before dependency' in e for e in errors))

    def test_missing_links_and_uncovered_criterion(self):
        self.data['tasks'][0]['criteria'] = ['AC-999']
        errors = self.errors()
        self.assertTrue(any('unknown ID AC-999' in e for e in errors))
        self.assertTrue(any('not covered by any active task' in e for e in errors))

    def test_duplicate_id_and_heading(self):
        self.data['requirements'].append(copy.deepcopy(self.data['requirements'][0]))
        with (self.feature / 'requirements.md').open('a') as file:
            file.write('### R-001: Duplicate\n')
        errors = self.errors()
        self.assertTrue(any('Duplicate ID' in e for e in errors))
        self.assertTrue(any('duplicate ID headings' in e for e in errors))

    def test_stale_is_not_task_state(self):
        self.data['tasks'][0]['state'] = 'stale'
        self.assertTrue(any('state' in e and 'stale' in e for e in self.errors()))

    def test_superseded_dependency_must_be_rewritten(self):
        old = copy.deepcopy(self.data['tasks'][0])
        old.update(id='T-002', state='superseded')
        self.data['tasks'].append(old)
        self.data['tasks'][0].update(depends_on=['T-002'], state='in-progress')
        self.assertTrue(any('before dependency' in e for e in self.errors()))

    def test_path_escape_and_overbroad_inputs(self):
        self.data['inputs'] = ['../escape']
        self.assertTrue(any('escapes project root' in e for e in self.errors()))
        self.data['inputs'] = ['.']
        self.assertTrue(any('contains the feature folder' in e for e in self.errors()))

    def test_check_is_read_only_and_does_not_execute_evidence(self):
        self.record()
        self.data['evidence'][0]['command'] = [sys.executable, '-c', 'open("UNWANTED", "w").write("x")']
        self.save()
        before = (self.feature / 'spec.json').read_bytes()
        result = self.cli('check', self.feature, '--root', self.root)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse((self.root / 'UNWANTED').exists())
        self.assertEqual((self.feature / 'spec.json').read_bytes(), before)

    def test_input_mutation_during_command_is_blocked(self):
        result = self.record('open("src/app.py", "w").write("VALUE = 2\\n")')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.data['evidence'][0]['outcome'], 'blocked')

    def test_timeout_records_blocked(self):
        result = self.cli('record', self.feature, '--root', self.root, '--timeout', '0.05', '--', sys.executable, '-c', 'import time; time.sleep(1)')
        self.assertEqual(result.returncode, 1)
        record = json.loads((self.feature / 'spec.json').read_text())['evidence'][0]
        self.assertEqual(record['outcome'], 'blocked')

    def test_newer_failure_overrides_prior_pass(self):
        self.record()
        self.done()
        self.record('assert False')
        self.assertTrue(any('no current passing acceptance' in e for e in self.errors(True)))

    def test_completed_feature_can_record_fresh_evidence_after_change(self):
        self.record()
        self.done()
        self.data['stage'] = 'complete'
        (self.root / 'src/app.py').write_text('VALUE = 1\n# changed implementation\n')
        result = self.record()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.done()
        self.assertEqual(self.errors(True), [])

    def test_manual_record_requires_actual_observation(self):
        result = self.cli('record', self.feature, '--root', self.root, '--criteria', 'AC-001', '--manual', 'Observed VALUE equals 1 in local Python REPL', '--outcome', 'pass')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.data = json.loads((self.feature / 'spec.json').read_text())
        self.done()
        self.assertEqual(self.errors(True), [])

    def test_malformed_json_cli_reports_error(self):
        (self.feature / 'spec.json').write_text('{broken')
        result = self.cli('check', self.feature, '--root', self.root)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_deleted_input_during_command_retains_blocked_history(self):
        self.data['inputs'] = ['src/app.py', 'tests']
        result = self.record('from pathlib import Path; Path("src/app.py").unlink()')
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(self.data['evidence'][0]['outcome'], 'blocked')
        self.assertTrue((self.root / self.data['evidence'][0]['log']).exists())

    def test_duplicate_record_criteria_rejected_before_execution(self):
        result = self.cli('record', self.feature, '--root', self.root, '--criteria', 'AC-001', 'AC-001', '--', sys.executable, '-c', 'open("UNWANTED", "w").write("x")')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'UNWANTED').exists())
        self.assertEqual(json.loads((self.feature / 'spec.json').read_text())['evidence'], [])

    def test_malformed_field_shapes_are_findings_not_tracebacks(self):
        for key, value in [('artifacts', []), ('artifacts', {'requirements': []}),
                           ('stage', []), ('mode', []), ('requirements', {}), ('tasks', [1]),
                           ('evidence', [{'id': 'E-001', 'outcome': [], 'criteria': []}])]:
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(self.data)
                changed[key] = value
                (self.feature / 'spec.json').write_text(json.dumps(changed))
                result = self.cli('check', self.feature, '--root', self.root)
                self.assertIn(result.returncode, (1, 2))
                self.assertNotIn('Traceback', result.stderr + result.stdout)

    def test_task_contract_change_invalidates_done_evidence(self):
        self.record()
        self.done()
        self.data['tasks'][0]['done_when'] = 'A different behavior is demonstrated'
        self.assertTrue(any('without current passing' in e for e in self.errors()))

    def test_task_prose_change_invalidates_done_evidence(self):
        self.record()
        self.done()
        with (self.feature / 'tasks.md').open('a') as file:
            file.write('Additional task scope.\n')
        self.assertTrue(any('without current passing' in e for e in self.errors()))

    def test_task_pause_boundary_is_validated_and_blocks_completion(self):
        self.data['pause_after_task'] = 'T-999'
        self.assertTrue(any('pause_after_task' in e for e in self.errors()))
        self.data['pause_after_task'] = 'T-001'
        self.record()
        self.done()
        self.assertEqual(self.errors(), [])
        self.assertTrue(any('pause_after_task' in e for e in self.errors(True)))

    def test_completion_requires_full_artifacts_even_at_early_stage(self):
        self.data['stage'] = 'requirements'
        del self.data['artifacts']['design']
        del self.data['artifacts']['tasks']
        self.data['tasks'] = []
        errors = self.errors(True)
        self.assertIn('Missing artifact record: design', errors)
        self.assertIn('Missing artifact record: tasks', errors)
        self.assertTrue(any('not covered by any active task' in e for e in errors))

    def test_schema_is_valid_json_and_current_fixture_matches(self):
        schema = json.loads(checker.SCHEMA.read_text(encoding='utf-8'))
        self.assertEqual(schema['$schema'], 'https://json-schema.org/draft/2020-12/schema')
        self.assertEqual(checker.schema_errors(self.data), [])

    def test_prose_only_planning_can_use_empty_runtime_inputs(self):
        self.data['stage'] = 'requirements'
        self.data['inputs'] = []
        errors, warnings = checker.validate(self.root, self.feature, self.data)
        self.assertEqual(errors, [])
        self.assertTrue(any('No runtime inputs' in w for w in warnings))
        self.assertTrue(any('declared runtime inputs' in e for e in self.errors(True)))

    def test_cli_requires_explicit_command_delimiter(self):
        result = self.cli('record', self.feature, '--root', self.root, sys.executable, '-c', 'open("UNWANTED", "w").write("x")')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'UNWANTED').exists())
        self.assertFalse((self.feature / '.spec-record.lock').exists())

    def test_cli_rejects_unknown_checker_option_instead_of_executing_it(self):
        result = self.cli('record', self.feature, '--root', self.root, '--timeuot', '1', '--', sys.executable, '-c', 'open("UNWANTED", "w").write("x")')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'UNWANTED').exists())

    def test_cli_rejects_nonfinite_timeout(self):
        for value in ['nan', 'inf', '-inf']:
            result = self.cli('record', self.feature, '--root', self.root, '--timeout', value, '--', sys.executable, '-c', 'pass')
            self.assertEqual(result.returncode, 2)

    def test_json_output_is_machine_readable_and_read_only(self):
        result = self.cli('check', self.feature, '--root', self.root, '--json')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data, {'valid': True, 'errors': [], 'warnings': []})

    def test_json_output_includes_unreadable_record_diagnostic(self):
        (self.feature / 'spec.json').write_text('{broken')
        result = self.cli('check', self.feature, '--root', self.root, '--json')
        self.assertEqual(result.returncode, 2)
        data = json.loads(result.stdout)
        self.assertFalse(data['valid'])
        self.assertTrue(data['errors'])

    def test_duplicate_json_keys_rejected(self):
        (self.feature / 'spec.json').write_text('{"schema_version": 2, "schema_version": 2}')
        result = self.cli('check', self.feature, '--root', self.root)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Duplicate JSON object key', result.stderr)

    def test_nonfinite_json_numbers_rejected(self):
        (self.feature / 'spec.json').write_text('{"schema_version": NaN}')
        result = self.cli('check', self.feature, '--root', self.root)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Non-finite JSON number', result.stderr)

    def test_utf8_bom_record_is_accepted(self):
        (self.feature / 'spec.json').write_text(json.dumps(self.data), encoding='utf-8-sig')
        result = self.cli('check', self.feature, '--root', self.root)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_unknown_core_property_rejected_but_extensions_allowed(self):
        self.data['stop_afer'] = 'verify'
        self.assertTrue(any('unknown property' in e for e in self.errors()))
        del self.data['stop_afer']
        self.data['extensions'] = {'team': {'ticket': 'APP-123'}}
        self.assertEqual(self.errors(), [])

    def test_malformed_nested_values_do_not_crash(self):
        for key in ['criteria', 'tasks', 'evidence']:
            for bad in [None, 0, 'text', [], {}, {'id': []}]:
                changed = copy.deepcopy(self.data)
                changed[key] = [bad]
                errors, _ = checker.validate(self.root, self.feature, changed)
                self.assertTrue(errors, (key, bad))

    def test_bad_utf8_prose_is_reported_without_traceback(self):
        (self.feature / 'requirements.md').write_bytes(b'\xff')
        result = self.cli('check', self.feature, '--root', self.root)
        self.assertIn(result.returncode, (1, 2))
        self.assertNotIn('Traceback', result.stderr + result.stdout)

    def test_concurrent_spec_change_is_preserved(self):
        result = self.record('import json; from pathlib import Path; p=Path("specs/feature/spec.json"); d=json.loads(p.read_text()); d["next_action"]="external edit"; p.write_text(json.dumps(d))')
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        self.assertEqual(self.data['next_action'], 'external edit')
        self.assertEqual(self.data['evidence'], [])
        self.assertTrue((self.feature / '.spec-evidence/E-001.log').exists())
        self.assertFalse((self.feature / '.spec-record.lock').exists())
        result = self.record()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.data['evidence'][0]['id'], 'E-002')

    def test_atomic_save_failure_leaves_original_record(self):
        destination = self.feature / 'spec.json'
        original = destination.read_bytes()
        changed = dict(self.data, next_action='new action')
        with patch.object(checker.os, 'replace', side_effect=OSError('simulated disk error')):
            with self.assertRaises(OSError):
                checker.atomic_save(self.feature, changed, original)
        self.assertEqual(destination.read_bytes(), original)
        self.assertFalse((self.feature / '.spec-record.tmp').exists())

    def test_interrupted_temporary_record_is_preserved_for_recovery(self):
        temporary = self.feature / '.spec-record.tmp'
        temporary.write_text('recoverable')
        result = self.record()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(temporary.read_text(), 'recoverable')
        self.assertEqual(self.data['evidence'], [])

    def test_interrupted_lock_is_not_silently_removed(self):
        lock = self.feature / '.spec-record.lock'
        lock.write_text('pid=unknown\n')
        result = self.record()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(lock.read_text(), 'pid=unknown\n')

    def test_concurrent_record_does_not_execute_second_command(self):
        command = [sys.executable, str(SCRIPT), 'record', str(self.feature), '--root', str(self.root), '--', sys.executable, '-c', 'import time; time.sleep(1)']
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not (self.feature / '.spec-record.lock').exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.feature / '.spec-record.lock').exists())
            second = self.cli('record', self.feature, '--root', self.root, '--', sys.executable, '-c', 'open("UNWANTED", "w").write("x")')
            self.assertEqual(second.returncode, 2)
            self.assertFalse((self.root / 'UNWANTED').exists())
            out, err = first.communicate(timeout=10)
            self.assertEqual(first.returncode, 0, err + out)
        finally:
            if first.poll() is None:
                first.kill()
                first.communicate()

    def test_newer_referenced_task_failure_cannot_be_hidden_by_old_pass(self):
        self.record()
        self.done()
        self.record('assert False')
        self.data['tasks'][0]['evidence'] = [e['id'] for e in self.data['evidence']]
        self.assertTrue(any('without current passing task evidence' in e for e in self.errors()))

    def test_unrelated_latest_task_evidence_is_not_inferred(self):
        self.record()
        self.done()
        # A task-only failing run is not implicitly linked to every task.
        self.save()
        self.cli('record', self.feature, '--root', self.root, '--', sys.executable, '-c', 'assert False')
        self.data = json.loads((self.feature / 'spec.json').read_text())
        self.assertEqual(self.errors(), [])

    def test_output_symlink_is_refused(self):
        unrelated = self.root / 'unrelated'
        unrelated.mkdir()
        link = self.feature / '.spec-evidence'
        try:
            link.symlink_to(unrelated, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Creating symlinks is unavailable in this environment')
        result = self.record()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(unrelated.iterdir()), [])

    def test_invalid_evidence_output_is_refused_before_execution(self):
        (self.feature / '.spec-evidence').write_text('existing user data')
        result = self.record('open("UNWANTED", "w").write("x")')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'UNWANTED').exists())
        self.assertEqual((self.feature / '.spec-evidence').read_text(), 'existing user data')

    def test_legitimate_empty_and_whitespace_arguments_remain_valid(self):
        result = self.cli('record', self.feature, '--root', self.root, '--criteria', 'AC-001', '--', sys.executable, '-c', 'import sys; assert sys.argv[1:] == ["", "  "]', '', '  ')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.data = json.loads((self.feature / 'spec.json').read_text())
        self.done()
        self.assertEqual(self.errors(True), [])

    def test_empty_executable_is_rejected_before_recording(self):
        result = self.cli('record', self.feature, '--root', self.root, '--', '')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads((self.feature / 'spec.json').read_text())['evidence'], [])

    def test_record_symlink_is_refused(self):
        destination = self.feature / 'spec.json'
        actual = self.feature / 'actual.json'
        actual.write_bytes(destination.read_bytes())
        destination.unlink()
        try:
            destination.symlink_to(actual)
        except (OSError, NotImplementedError):
            destination.write_bytes(actual.read_bytes())
            self.skipTest('Creating symlinks is unavailable in this environment')
        result = self.cli('record', self.feature, '--root', self.root, '--', sys.executable, '-c', 'open("UNWANTED", "w").write("x")')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'UNWANTED').exists())

    def test_large_dependency_chain_does_not_exceed_recursion_limit(self):
        self.data['tasks'] = []
        prose = '# Tasks\n'
        for number in range(1, 1201):
            key = f'T-{number:03}'
            self.data['tasks'].append({'id': key, 'state': 'pending', 'depends_on': [] if number == 1 else [f'T-{number - 1:03}'], 'requirements': ['R-001'], 'criteria': ['AC-001'], 'done_when': 'Expected behavior', 'evidence': []})
            prose += f'## {key}: Scope\nTask scope.\n'
        (self.feature / 'tasks.md').write_text(prose)
        self.assertEqual(self.errors(), [])
        self.data['tasks'][0]['depends_on'] = ['T-1200']
        self.assertTrue(any('cycle' in e for e in self.errors()))


if __name__ == '__main__':
    unittest.main()
