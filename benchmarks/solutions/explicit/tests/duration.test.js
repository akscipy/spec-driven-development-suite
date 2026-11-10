import test from 'node:test';
import assert from 'node:assert/strict';
import {parseDuration} from '../src/duration.js';
test('existing single durations', () => {
  assert.equal(parseDuration('2h'), 7200);
  assert.equal(parseDuration('15m'), 900);
  assert.equal(parseDuration('45s'), 45);
});

test('compound durations and skipped units return total seconds', () => {
  for (const [input, expected] of [
    ['1d', 86400],
    ['1d2h3m4s', 93784],
    ['2d4s', 172804],
    ['1h2m', 3720],
    ['2m3s', 123],
    ['90m', 5400],
    ['1h60m', 7200],
  ]) {
    assert.equal(parseDuration(input), expected, input);
  }
});

test('uppercase units and whitespace around and between components are accepted', () => {
  for (const input of ['1D2H3M4S', '  1d 2H 3m 4S  ', '\t1D\n2h\t3M\r\n4s\n']) {
    assert.equal(parseDuration(input), 93784, input);
  }
});

test('zero and leading zero amounts are valid', () => {
  for (const input of ['0d', '0h', '0m', '0s', '0d0h0m0s', '000s']) {
    assert.equal(parseDuration(input), 0, input);
  }
  assert.equal(parseDuration('001d02h03m04s'), 93784);
});

test('empty input, bare numbers, signs, decimals and unknown units are rejected', () => {
  for (const input of ['', ' \t\n', '1', '0', '+1h', '-1h', '1h-2m', '1h+2m', '1.5h', '.5h', '1e3s', '0x10s', '1w', '1ms', '1H2x']) {
    assert.throws(() => parseDuration(input), RangeError, input);
  }
});

test('repeated or out-of-order units are rejected including zero amounts', () => {
  const units = ['d', 'h', 'm', 's'];
  for (let first = 0; first < units.length; first++) {
    for (let second = 0; second < units.length; second++) {
      const input = `1${units[first]}2${units[second]}`;
      if (first >= second) {
        assert.throws(() => parseDuration(input), RangeError, input);
      } else {
        const seconds = [86400, 3600, 60, 1];
        assert.equal(parseDuration(input), seconds[first] + 2 * seconds[second], input);
      }
    }
  }
  for (const input of ['0h0h', '0s0d', '1d2h3d', '1h2H', '1s0m']) {
    assert.throws(() => parseDuration(input), RangeError, input);
  }
});

test('junk and whitespace inside a component are rejected', () => {
  for (const input of ['junk1h', '1hjunk', '1h,2m', '1h/2m', '1h 2', '1 h', '1d2 h', '1\n2s', '1h\u00002m', '1h2m!']) {
    assert.throws(() => parseDuration(input), RangeError, input);
  }
});

test('non-string input throws TypeError without coercion', () => {
  for (const input of [undefined, null, 0, 12, 1n, true, [], {}, new String('1h'), Symbol('1h'), () => '1h']) {
    assert.throws(() => parseDuration(input), TypeError);
  }
  const coercible = {toString() { throw new Error('Must not coerce'); }};
  assert.throws(() => parseDuration(coercible), TypeError);
});

test('safe integer limit is enforced for single and compound totals', () => {
  const max = BigInt(Number.MAX_SAFE_INTEGER);
  assert.equal(parseDuration(`${max}s`), Number.MAX_SAFE_INTEGER);
  assert.equal(parseDuration(`000${max}s`), Number.MAX_SAFE_INTEGER);
  assert.throws(() => parseDuration(`${max + 1n}s`), RangeError);

  for (const [unit, scale] of [['d', 86400n], ['h', 3600n], ['m', 60n]]) {
    const amount = max / scale;
    const remainder = max % scale;
    assert.equal(parseDuration(`${amount}${unit}${remainder}s`), Number.MAX_SAFE_INTEGER);
    assert.throws(() => parseDuration(`${amount}${unit}${remainder + 1n}s`), RangeError);
    assert.throws(() => parseDuration(`${amount + 1n}${unit}`), RangeError);
  }
  assert.throws(() => parseDuration(`${'9'.repeat(400)}s`), RangeError);
});
