import test from 'node:test';
import assert from 'node:assert/strict';
import {parseDuration} from '../src/duration.js';
test('existing single durations', () => {
  assert.equal(parseDuration('2h'), 7200);
  assert.equal(parseDuration('15m'), 900);
  assert.equal(parseDuration('42s'), 42);
});

test('compound durations accept days, uppercase units, and component whitespace', () => {
  for (const text of ['1d2h3m4s', '1D2H3M4S', ' \t1d 2H\n3m\t4S\r\n']) {
    assert.equal(parseDuration(text), 93784, text);
  }
  assert.equal(parseDuration('2d'), 172800);
  assert.equal(parseDuration('1d30s'), 86430);
  assert.equal(parseDuration('2h90m'), 12600);
  assert.equal(parseDuration('001h02m'), 3720);
});

test('zero amounts and totals are valid', () => {
  for (const text of ['0d', '0h', '0m', '0s', '0d0h0m0s', ' 000S ']) {
    assert.equal(parseDuration(text), 0, text);
  }
  assert.equal(parseDuration('0d1h0m1s'), 3601);
});

test('invalid syntax throws RangeError', () => {
  for (const text of [
    '', ' \t\n', '12', '+1h', '-1s', '1.5h', '.5h', '1e2s',
    '1w', '1day', '1h2', '1 h', '1h 2 m', 'h', '1h,2m', '1h+2m',
    'junk1h', '1h junk 2m', '1h2ms', '1h\u00002m',
  ]) {
    assert.throws(() => parseDuration(text), RangeError, JSON.stringify(text));
  }
});

test('units must be unique and in descending order even for zero amounts', () => {
  for (const text of [
    '1d1d', '1h1H', '1m 2m', '0s0s', '1h1d', '1m1h', '1s1m',
    '1d1m1h', '0s0d', '1d0h1d',
  ]) {
    assert.throws(() => parseDuration(text), RangeError, text);
  }
});

test('non-string inputs throw TypeError without coercion', () => {
  for (const value of [undefined, null, 0, 3600, true, 1n, Symbol('1h'), [], {}, new String('1h')]) {
    assert.throws(() => parseDuration(value), TypeError);
  }
  assert.throws(() => parseDuration({toString() { throw new Error('Must not coerce'); }}), TypeError);
});

test('totals must be safe integers including multiplication and compound addition', () => {
  assert.equal(parseDuration('9007199254740991s'), Number.MAX_SAFE_INTEGER);
  assert.equal(parseDuration('150119987579016m31s'), Number.MAX_SAFE_INTEGER);
  assert.equal(parseDuration('150119987579016m'), 9007199254740960);
  for (const text of [
    '9007199254740992s', '9007199254740993s', '150119987579017m',
    '150119987579016m32s', '9007199254740991d', `${'9'.repeat(400)}s`,
  ]) {
    assert.throws(() => parseDuration(text), RangeError, text);
  }
});
