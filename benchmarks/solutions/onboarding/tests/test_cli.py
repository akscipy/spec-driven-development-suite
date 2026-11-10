import json
from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def invoke(self, stdin, *args):
        return subprocess.run(
            [sys.executable, "-m", "src.cli", *args],
            input=stdin, text=True, capture_output=True,
            cwd=PROJECT_ROOT, timeout=10,
        )

    def assert_error(self, stdin, args, message):
        result = self.invoke(stdin, *args)
        self.assertEqual(result.returncode, 2, result)
        self.assertEqual(result.stdout, "")
        self.assertIn(message, result.stderr)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_ranks_json_with_stable_ties_and_extra_fields(self):
        items = [{"id": "low", "priority": 0, "extra": [1]},
                 {"id": "first", "priority": 2},
                 {"id": "second", "priority": 2}]
        result = self.invoke(json.dumps(items))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), [items[1], items[2], items[0]])

    def test_optional_limit(self):
        items = [{"id": "a", "priority": 1}, {"id": "b", "priority": 3}]
        for limit, expected in ((1, [items[1]]), (2, [items[1], items[0]]),
                                (10, [items[1], items[0]])):
            with self.subTest(limit=limit):
                result = self.invoke(json.dumps(items), "--limit", str(limit))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(json.loads(result.stdout), expected)

    def test_empty_list(self):
        for args in ((), ("--limit", "1")):
            with self.subTest(args=args):
                result = self.invoke("[]", *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "[]")
                self.assertEqual(result.stderr, "")

    def test_malformed_json(self):
        for stdin in ("", "[", "[] trailing"):
            with self.subTest(stdin=stdin):
                self.assert_error(stdin, (), "invalid JSON")

    def test_invalid_collections(self):
        for stdin in ("null", "{}", '"items"', "1", "true"):
            with self.subTest(stdin=stdin):
                self.assert_error(stdin, (), "items must be a list")

    def test_invalid_items(self):
        invalid_cases = [([None], "item 0 must be a dictionary"),
                         ([{}], "id must be a nonempty string"),
                         ([{"id": "", "priority": 0}], "id must be a nonempty string"),
                         ([{"id": "a", "priority": True}], "priority must be a nonnegative integer"),
                         ([{"id": "a", "priority": -1}], "priority must be a nonnegative integer")]
        for items, message in invalid_cases:
            with self.subTest(items=items):
                self.assert_error(json.dumps(items), (), message)

    def test_invalid_trailing_item_and_duplicate_after_limit(self):
        head = {"id": "a", "priority": 100}
        for tail, message in (({"id": "b", "priority": -1}, "item 1 priority"),
                              ({"id": "a", "priority": 0}, "duplicate id")):
            with self.subTest(tail=tail):
                self.assert_error(json.dumps([head, tail]), ("--limit", "1"), message)

    def test_nonpositive_limit(self):
        for limit in ("0", "-1"):
            with self.subTest(limit=limit):
                self.assert_error("[]", ("--limit", limit), "limit must be greater than zero")

    def test_argument_errors(self):
        cases = [(("--limit", "true"), "invalid int value"),
                 (("--limit", "1.5"), "invalid int value"),
                 (("--limit",), "expected one argument"),
                 (("--unknown",), "unrecognized arguments"),
                 (("extra",), "unrecognized arguments")]
        for args, message in cases:
            with self.subTest(args=args):
                self.assert_error("[]", args, message)


if __name__ == "__main__":
    unittest.main()
