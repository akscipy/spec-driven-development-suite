export function parseDuration(text) {
  if (typeof text !== 'string') throw new TypeError('Duration must be a string');

  const value = text.trim().toLowerCase();
  if (!/^\d+[dhms](?:\s*\d+[dhms])*$/.test(value)) {
    throw new RangeError('Invalid duration');
  }

  const secondsPerUnit = {d: 86400, h: 3600, m: 60, s: 1};
  let previousUnit = Infinity;
  let total = 0;
  for (const [, amount, unit] of value.matchAll(/(\d+)([dhms])/g)) {
    const seconds = secondsPerUnit[unit];
    if (seconds >= previousUnit) throw new RangeError('Invalid duration units');
    total += Number(amount) * seconds;
    if (!Number.isSafeInteger(total)) throw new RangeError('Duration is too large');
    previousUnit = seconds;
  }
  return total;
}
