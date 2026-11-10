export function parseDuration(text) {
  if (typeof text !== 'string') throw new TypeError('Duration must be a string');

  const duration = text.trim();
  if (!duration) throw new RangeError('Invalid duration');

  const secondsPerUnit = {d: 86400, h: 3600, m: 60, s: 1};
  const component = /(\d+)([dhms])\s*/iy;
  let position = 0;
  let previousUnit = Infinity;
  let total = 0;

  while (position < duration.length) {
    component.lastIndex = position;
    const match = component.exec(duration);
    if (!match) throw new RangeError('Invalid duration');

    const unit = secondsPerUnit[match[2].toLowerCase()];
    if (unit >= previousUnit) throw new RangeError('Invalid duration');

    total += Number(match[1]) * unit;
    if (!Number.isSafeInteger(total)) throw new RangeError('Duration is too large');

    previousUnit = unit;
    position = component.lastIndex;
  }

  return total;
}
