/** Normalize Vietnamese search text without changing the displayed label. */
export function normalizeSearch(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase().trim();
}

/** Parse a local HH:MM value; never send a time-only string to Date.parse(). */
export function parseTime(value: string): Date | null {
  const match = /^(\d{2}):(\d{2})$/.exec(value);
  if (!match) return null;
  const hours = Number(match[1]); const minutes = Number(match[2]);
  return hours < 24 && minutes < 60 ? new Date(2000, 0, 1, hours, minutes, 0, 0) : null;
}

export function timeLabel(value: string): string {
  return parseTime(value) ? value : 'Chọn giờ';
}
