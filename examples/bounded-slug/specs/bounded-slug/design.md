# Bounded slug design

The standard-library function in src/slugs.py owns argument validation, ASCII filtering, normalization, truncation, and trailing-separator cleanup. Filter before lowercasing to avoid introducing ASCII characters through Unicode case conversion. R-001 is covered by AC-001 and AC-002; R-002 is covered by AC-003.

Use unittest tests in tests/test_slugs.py. No persistence, external dependency, or migration is needed. The supplied implementation is a working teaching example. Its task record deliberately starts pending: run checks and inspect their results before recording completion.
