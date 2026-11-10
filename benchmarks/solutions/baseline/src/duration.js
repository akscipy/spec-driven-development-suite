export function parseDuration(text) {
  if (typeof text !== 'string') throw new TypeError('Duration must be a string');

  const input = text.trim();
  if (!input) throw new RangeError('Invalid duration');

  const units = ['d', 'h', 'm', 's'];
  const secondsPerUnit = [86400, 3600, 60, 1];
  const component = /(\d+)([dhms])\s*/giy;
  let position = 0;
  let previousUnit = -1;
  let total = 0;

  while (position < input.length) {
    component.lastIndex = position;
    const match = component.exec(input);
    if (!match) throw new RangeError('Invalid duration');

    const unit = units.indexOf(match[2].toLowerCase());
    if (unit <= previousUnit) throw new RangeError('Invalid duration');

    const amount = Number(match[1]);
    const seconds = amount * secondsPerUnit[unit];
    if (!Number.isSafeInteger(seconds) || !Number.isSafeInteger(total + seconds)) {
      throw new RangeError('Duration exceeds the safe integer range');
    }

    total += seconds;
    previousUnit = unit;
    position = component.lastIndex;
  }

  return total;
}
