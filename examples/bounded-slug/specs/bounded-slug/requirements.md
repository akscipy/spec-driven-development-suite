# Bounded ASCII slugs

### R-001: Normalize a bounded slug

Accept string input and return a lowercase ASCII slug. Replace every run of characters outside ASCII A-Z, a-z, and 0-9 with one hyphen and trim edge hyphens. Do not transliterate Unicode characters. Truncate the normalized slug to max_length and remove a trailing hyphen produced by truncation. The default bound is 80; empty or punctuation-only input returns an empty string.

### R-002: Reject invalid arguments

Reject non-string text and non-integer bounds, including booleans, with TypeError. Reject integer bounds below 1 with ValueError, even for empty text. Validate argument types and values before normalization.

### AC-001 (R-001)

`slugify(' Hello, WORLD!! ')` returns `hello-world`; `a---b__c` becomes `a-b-c`; empty and punctuation-only inputs return an empty string. `caf\u00e9` becomes `caf`; `\u0130stanbul` becomes `stanbul` because only ASCII letters are retained.

### AC-002 (R-001)

An 81-character ASCII word becomes 80 characters by default and stays 81 with max_length=100. `slugify('hello world', 6)` returns `hello`; bound 7 returns `hello-w`; bound 1 returns `h`.

### AC-003 (R-002)

Bounds 0 and -1 raise ValueError for both nonempty and empty input. Boolean, float, string and null bounds raise TypeError. Non-string text raises TypeError.
