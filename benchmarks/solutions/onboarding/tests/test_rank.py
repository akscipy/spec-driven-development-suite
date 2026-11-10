import copy
import unittest

from src.rank import rank_items


class RankTests(unittest.TestCase):
    def test_empty(self):
        items = []
        for limit in (None, 1, 5):
            with self.subTest(limit=limit):
                result = rank_items(items, limit)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)

    def test_stable_descending_order_and_no_mutation(self):
        items = [
            {"id": "a", "priority": 1, "metadata": {"tags": ["keep"]}},
            {"id": "b", "priority": 4},
            {"id": "c", "priority": 4},
            {"id": "d", "priority": 0},
            {"id": "e", "priority": 1},
        ]
        before = copy.deepcopy(items)
        original_objects = list(items)
        result = rank_items(items)
        self.assertEqual([item["id"] for item in result], ["b", "c", "a", "e", "d"])
        self.assertIsNot(result, items)
        self.assertEqual(items, before)
        for item, original in zip(items, original_objects):
            self.assertIs(item, original)
        self.assertIs(result[2], items[0])
        self.assertEqual(rank_items(items), result)

    def test_limit_prefixes_and_input_preservation(self):
        items = [{"id": "a", "priority": 0}, {"id": "b", "priority": 3},
                 {"id": "c", "priority": 3}]
        before = copy.deepcopy(items)
        for limit, expected in ((None, ["b", "c", "a"]), (1, ["b"]),
                                (2, ["b", "c"]), (3, ["b", "c", "a"]),
                                (10, ["b", "c", "a"])):
            with self.subTest(limit=limit):
                result = rank_items(items, limit)
                self.assertEqual([item["id"] for item in result], expected)
                self.assertIsNot(result, items)
                self.assertEqual(items, before)

    def test_valid_boundary_values_and_extra_fields(self):
        items = [{"id": " ", "priority": 0, "other": [1]},
                 {"id": "large", "priority": 10 ** 100}]
        self.assertEqual(rank_items(items), [items[1], items[0]])
        self.assertEqual(rank_items(items)[1]["other"], [1])

    def test_invalid_item_shapes_and_ids(self):
        invalid_items = [None, [], 1, True, "item", {}, {"priority": 1},
                         {"id": "", "priority": 1}, {"id": None, "priority": 1},
                         {"id": 1, "priority": 1}, {"id": True, "priority": 1},
                         {"id": [], "priority": 1}]
        for invalid in invalid_items:
            with self.subTest(item=invalid):
                with self.assertRaisesRegex(ValueError, "item 0"):
                    rank_items([invalid])

    def test_invalid_priorities(self):
        for priority in (None, -1, 1.0, "1", True, False, [], {}):
            with self.subTest(priority=priority):
                with self.assertRaisesRegex(ValueError, "priority"):
                    rank_items([{"id": "a", "priority": priority}])
        with self.assertRaisesRegex(ValueError, "priority"):
            rank_items([{"id": "a"}])

    def test_duplicate_ids(self):
        items = [{"id": "same", "priority": 1}, {"id": "same", "priority": 2}]
        with self.assertRaisesRegex(ValueError, "duplicate id"):
            rank_items(items)

    def test_validation_is_not_limited_to_output(self):
        head = {"id": "a", "priority": 100}
        for tail in (None, {"id": "b", "priority": -1},
                     {"id": "a", "priority": 0}):
            with self.subTest(tail=tail):
                items = [head, tail]
                before = copy.deepcopy(items)
                with self.assertRaisesRegex(ValueError, "item 1"):
                    rank_items(items, limit=1)
                self.assertEqual(items, before)

    def test_items_must_be_a_list(self):
        for items in (None, (), {}, "[]", iter([])):
            with self.subTest(items=items):
                with self.assertRaisesRegex(TypeError, "items must be a list"):
                    rank_items(items)

    def test_limit_types(self):
        for limit in (True, False, 1.0, "1", [], {}):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(TypeError, "limit"):
                    rank_items([], limit)

    def test_limit_must_be_positive(self):
        for limit in (0, -1, -10):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, "limit"):
                    rank_items([], limit)


if __name__ == "__main__":
    unittest.main()
