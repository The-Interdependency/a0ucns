const LETTERS = 'abcdefghijklmnopqrstuvwxyz';

export function generateInstanceName() {
  let letters = '';
  let digits = '';
  for (let index = 0; index < 4; index += 1) {
    letters += LETTERS[Math.floor(Math.random() * LETTERS.length)];
    digits += Math.floor(Math.random() * 10).toString();
  }
  return `${letters}${digits}`;
}
