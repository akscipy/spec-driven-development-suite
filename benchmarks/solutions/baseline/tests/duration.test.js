import test from 'node:test';
import assert from 'node:assert/strict';
import {parseDuration} from '../src/duration.js';
test('existing single durations', () => {
  assert.equal(parseDuration('2h'), 7200);
  assert.equal(parseDuration('15m'), 900);
});

test('valid compound durations and flexible component spacing', () => {
  const cases = [
    ['1d2h3m4s', 93784],
    ['1d 2h 3m 4s', 93784],
    [' \t1D 2h\n3M\t4S\r\n', 93784],
    ['1d30s', 86430],
    ['2h90m', 12600],
    ['001D002H003M004S', 93784],
    ['1s', 1],
    [' 2H ', 7200],
    ['0d0h0m0s', 0],
    ['0s', 0],
    ['0d', 0],
  ];
  for (const [input, expected] of cases) {
    assert.equal(parseDuration(input), expected, input);
  }
});

test('invalid duration strings throw RangeError', () => {
  const cases = [
    '', ' ', '\t\n', '0', '123',
    '-1h', '+1s', '1.5h', '.5s', '1e3s',
    '1w', '1ms', '1hour',
    '1h2h', '1H2h', '0s0s', '1m1h', '1s1d', '0s0m',
    '1 h', '1d 2 h', '1h,2m', '1h and 2m', 'x1h', '1hx',
    '1h2', '1h-2m', '1h+2m', '1h2.5m', '1h\u00002m',
  ];
  for (const input of cases) {
    assert.throws(() => parseDuration(input), RangeError, JSON.stringify(input));
  }
});

test('non-string inputs throw TypeError without coercion', () => {
  const cases = [undefined, null, 0, 1, NaN, true, 1n, Symbol('1s'), [], {}, new String('1s')];
  for (const input of cases) {
    assert.throws(() => parseDuration(input), TypeError);
  }
  assert.throws(() => parseDuration({toString() { throw new Error('must not coerce'); }}), TypeError);
});

test('safe integer limits are enforced for components and totals', () => {
  assert.equal(parseDuration('9007199254740991s'), Number.MAX_SAFE_INTEGER);
  assert.equal(parseDuration('150119987579016m31s'), Number.MAX_SAFE_INTEGER);
  assert.equal(parseDuration('150119987579016m'), 9007199254740960);

  for (const input of [
    '9007199254740992s',
    '9007199254740993s',
    '150119987579017m',
    '150119987579016m32s',
    '9007199254740991d',
    `${'9'.repeat(400)}s`,
  ]) {
    assert.throws(() => parseDuration(input), RangeError, input);
  }
});
