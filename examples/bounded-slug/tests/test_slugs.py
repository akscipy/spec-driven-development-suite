import unittest
from src.slugs import slugify


class SlugTests(unittest.TestCase):
    def test_ascii_normalization(self):
        self.assertEqual(slugify(' Hello, WORLD!! '), 'hello-world')
        self.assertEqual(slugify('a---b__c'), 'a-b-c')
        self.assertEqual(slugify('caf\u00e9'), 'caf')
        self.assertEqual(slugify('\u0130stanbul'), 'stanbul')

    def test_empty_and_punctuation(self):
        self.assertEqual(slugify(''), '')
        self.assertEqual(slugify('!!!'), '')

    def test_default_and_explicit_bounds(self):
        self.assertEqual(slugify('a' * 81), 'a' * 80)
        self.assertEqual(slugify('a' * 81, max_length=100), 'a' * 81)
        self.assertEqual(slugify('hello world', 6), 'hello')
        self.assertEqual(slugify('hello world', 7), 'hello-w')
        self.assertEqual(slugify('hello', 1), 'h')

    def test_invalid_bound_values(self):
        for text in ('hello', ''):
            for bound in (0, -1):
                with self.subTest(text=text, bound=bound):
                    with self.assertRaises(ValueError):
                        slugify(text, bound)

    def test_invalid_types(self):
        for value in (True, False, 1.0, '4', None):
            with self.subTest(bound=value):
                with self.assertRaises(TypeError):
                    slugify('', value)
        for value in (None, 1, [], {}):
            with self.subTest(text=value):
                with self.assertRaises(TypeError):
                    slugify(value)


if __name__ == '__main__':
    unittest.main()
