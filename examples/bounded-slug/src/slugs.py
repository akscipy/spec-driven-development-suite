"""Bounded ASCII slugs used by a route naming layer."""
import re


def slugify(text, max_length=80):
    if not isinstance(text, str):
        raise TypeError('text must be a string')
    if isinstance(max_length, bool) or not isinstance(max_length, int):
        raise TypeError('max_length must be an integer, excluding booleans')
    if max_length < 1:
        raise ValueError('max_length must be positive')
    # Filter to ASCII before case conversion: no Unicode transliteration is implied.
    slug = re.sub(r'[^A-Za-z0-9]+', '-', text).lower().strip('-')
    return slug[:max_length].rstrip('-')
