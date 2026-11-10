"""Ensure acceptance scoring rejects the original incomplete fixture."""
import importlib.util
from pathlib import Path
import shutil
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot', ROOT / 'benchmarks/run_benchmark.py')
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.scratch = ROOT / 'tests/.runs' / uuid.uuid4().hex
        self.scratch.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)

    @unittest.skipUnless(shutil.which('node'), 'Node required for JavaScript acceptance scoring')
    def test_incomplete_seed_cannot_pass_acceptance(self):
        pilot.prepare(self.scratch / 'cases')
        result = pilot.score(self.scratch / 'cases/baseline')
        self.assertLess(result['passed'], result['total'])
        failures = {c['name'] for c in result['checks'] if not c['pass']}
        self.assertIn('compound', failures)
        self.assertIn('type', failures)
        self.assertIn('safe-integer', failures)

    def test_prepare_refuses_existing_outputs_before_any_writes(self):
        (self.scratch / 'cases/explicit').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'Preserve existing run'):
            pilot.prepare(self.scratch / 'cases')
        self.assertFalse((self.scratch / 'cases/baseline').exists())


if __name__ == '__main__':
    unittest.main()
