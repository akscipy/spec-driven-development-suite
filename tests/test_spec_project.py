"""Initializer and runnable-example checks in isolated workspace directories."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/spec-workflow/scripts/spec_project.py'
spec = importlib.util.spec_from_file_location('spec_project', SCRIPT)
project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.scratch = ROOT / 'tests/.runs' / uuid.uuid4().hex
        self.scratch.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.root = self.scratch / 'project'
        self.root.mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/app.py').write_text('VALUE = 1\n', encoding='utf-8')

    def init(self, **overrides):
        options = dict(root=self.root, feature='invite-users', goal='Owner can invite a teammate',
                       criterion='A valid email creates an invitation')
        options.update(overrides)
        return project.initialize(**options)

    def test_minimal_initialization_is_valid_draft_not_claimed_work(self):
        feature = self.init()
        self.assertEqual({p.name for p in feature.iterdir()}, {'requirements.md', 'spec.json'})
        data = json.loads((feature / 'spec.json').read_text(encoding='utf-8'))
        self.assertEqual(data['mode'], 'autonomous')
        self.assertEqual(data['stage'], 'requirements')
        self.assertEqual(data['stop_after'], 'requirements')
        self.assertEqual(data['artifacts']['requirements']['status'], 'draft')
        self.assertEqual(data['tasks'], [])
        self.assertEqual(data['evidence'], [])
        self.assertNotIn('approval', data['artifacts']['requirements'])
        errors, warnings = project.checker_module().validate(self.root, feature, data)
        self.assertEqual(errors, [])
        self.assertTrue(any('inputs' in text for text in warnings))

    def test_guided_mode_inputs_and_unicode_preserve_project(self):
        original = (self.root / 'src/app.py').read_bytes()
        feature = self.init(mode='guided', inputs=['src'], goal='Inviter un co\u00e9quipier')
        data = json.loads((feature / 'spec.json').read_text(encoding='utf-8'))
        self.assertEqual(data['mode'], 'guided')
        self.assertEqual(data['inputs'], ['src'])
        self.assertEqual((self.root / 'src/app.py').read_bytes(), original)
        self.assertIn('co\u00e9quipier', (feature / 'requirements.md').read_text(encoding='utf-8'))

    def test_existing_empty_or_populated_feature_is_never_overwritten(self):
        feature = self.root / 'specs/invite-users'
        feature.mkdir(parents=True)
        for populated in (False, True):
            with self.subTest(populated=populated):
                if populated:
                    (feature / 'notes.txt').write_text('preserve me')
                with self.assertRaisesRegex(project.ProjectError, 'already exists'):
                    self.init()
        self.assertEqual((feature / 'notes.txt').read_text(), 'preserve me')
        self.assertFalse((feature / 'spec.json').exists())

    def test_invalid_feature_names_create_nothing(self):
        for value in ('../escape', 'a/b', '.', '', 'Upper', 'a b', '-start', 'con', 'nul', 'x' * 65):
            with self.subTest(value=value):
                with self.assertRaises(project.ProjectError):
                    self.init(feature=value)
        self.assertFalse((self.root / 'specs').exists())

    def test_missing_root_is_not_created(self):
        missing = self.scratch / 'missing'
        with self.assertRaisesRegex(project.ProjectError, 'existing project'):
            self.init(root=missing)
        self.assertFalse(missing.exists())

    def test_empty_text_inputs_and_bad_mode_are_rejected(self):
        for values in ({'goal': ' '}, {'criterion': '\n'}, {'inputs': [' ']},
                       {'inputs': ['src', 'src']}, {'inputs': ['src', 'src/']}, {'mode': 'unknown'}):
            with self.subTest(values=values):
                with self.assertRaises(project.ProjectError):
                    self.init(**values)
        self.assertFalse((self.root / 'specs').exists())

    def test_missing_escaping_or_overbroad_inputs_are_rejected(self):
        for values in (['missing'], ['../outside'], [str(self.root / 'src')], ['.']):
            with self.subTest(values=values):
                with self.assertRaises(project.ProjectError):
                    self.init(inputs=values)
        self.assertFalse((self.root / 'specs').exists())

    def test_multiline_user_text_cannot_introduce_registered_headings(self):
        feature = self.init(goal='Invite users\n### R-999: supplied heading',
                            criterion='Valid email\n### AC-999 (R-999)\nLiteral user text')
        data = json.loads((feature / 'spec.json').read_text(encoding='utf-8'))
        errors, _ = project.checker_module().validate(self.root, feature, data)
        self.assertEqual(errors, [])
        self.assertIn('> ### R-999', (feature / 'requirements.md').read_text(encoding='utf-8'))

    def test_partial_write_failure_removes_only_its_own_artifacts(self):
        (self.root / 'specs').mkdir()
        marker = self.root / 'specs/existing.txt'
        marker.write_text('keep')
        original = Path.open

        def fail_spec(path, *args, **kwargs):
            if path.name == 'spec.json' and args and args[0] == 'x':
                raise OSError('simulated disk failure')
            return original(path, *args, **kwargs)

        with patch.object(Path, 'open', fail_spec):
            with self.assertRaisesRegex(OSError, 'simulated disk failure'):
                self.init()
        self.assertEqual(marker.read_text(), 'keep')
        self.assertFalse((self.root / 'specs/invite-users').exists())

    def test_checker_failure_rolls_back_new_record(self):
        class FailingChecker:
            @staticmethod
            def validate(*args):
                return ['simulated invalid draft'], []
        with patch.object(project, 'checker_module', return_value=FailingChecker):
            with self.assertRaisesRegex(project.ProjectError, 'simulated invalid draft'):
                self.init()
        self.assertFalse((self.root / 'specs').exists())

    def test_cleanup_preserves_content_added_during_failed_validation(self):
        class ConcurrentWriter:
            @staticmethod
            def validate(root, feature, data):
                (feature / 'user-note.txt').write_text('written by another process')
                return ['record invalid'], []
        with patch.object(project, 'checker_module', return_value=ConcurrentWriter):
            with self.assertRaises(project.ProjectError):
                self.init()
        feature = self.root / 'specs/invite-users'
        self.assertEqual((feature / 'user-note.txt').read_text(), 'written by another process')
        self.assertFalse((feature / 'spec.json').exists())
        self.assertFalse((feature / 'requirements.md').exists())

    def test_redirected_output_is_rejected_before_writes(self):
        original = Path.is_symlink
        specs = self.root / 'specs'
        with patch.object(Path, 'is_symlink', lambda path: path == specs or original(path)):
            with self.assertRaisesRegex(project.ProjectError, 'Redirected path'):
                self.init()
        self.assertFalse(specs.exists())

    def test_source_symlink_escape_is_rejected(self):
        external = self.scratch / 'external'
        external.mkdir()
        link = self.root / 'linked'
        try:
            link.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Creating symlinks is unavailable in this environment')
        with self.assertRaisesRegex(project.ProjectError, 'Redirected path'):
            self.init(inputs=['linked'])
        self.assertFalse((self.root / 'specs').exists())

    def test_cli_reports_invalid_input_without_traceback(self):
        run = subprocess.run([sys.executable, str(SCRIPT), 'init', '--root', str(self.root),
                              '--feature', '../escape', '--goal', 'Invite', '--criterion', 'Valid invitation'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn('Traceback', run.stderr)
        self.assertFalse((self.root / 'specs').exists())

    def test_runnable_example_captures_actual_evidence_without_mutating_source(self):
        source = ROOT / 'examples/bounded-slug'
        before = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        output = self.scratch / 'demo'
        run = subprocess.run([sys.executable, '-B', str(ROOT / 'examples/demo.py'), '--workspace', str(output)],
                             capture_output=True, text=True, timeout=90)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        summary = json.loads(run.stdout)
        self.assertTrue(summary['completion']['valid'])
        record = json.loads((output / 'specs/bounded-slug/spec.json').read_text(encoding='utf-8'))
        self.assertEqual([item['outcome'] for item in record['evidence']], ['pass', 'pass'])
        self.assertTrue(all(task['state'] == 'done' for task in record['tasks']))
        self.assertTrue((output / record['evidence'][0]['log']).is_file())
        after = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(before, after)

    def test_demo_refuses_existing_workspace(self):
        output = self.scratch / 'existing'
        output.mkdir()
        marker = output / 'notes.txt'
        marker.write_text('keep')
        run = subprocess.run([sys.executable, '-B', str(ROOT / 'examples/demo.py'), '--workspace', str(output)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(marker.read_text(), 'keep')
        self.assertFalse((output / 'src').exists())


if __name__ == '__main__':
    unittest.main()
