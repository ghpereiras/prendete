// Always renders weekday + day-month-year (e.g. "Vie 25 sep 2026"), regardless of the
// runtime locale's usual field order (some put month first, others day
// first) — that ambiguity is exactly what this format avoids.
export function formatDate(dateInput: string | Date, locale: string): string {
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput;
  const shortWeekday = new Intl.DateTimeFormat(locale, { weekday: "short" }).format(date).replace(".", "").slice(0, 3);
  const weekday = shortWeekday.charAt(0).toUpperCase() + shortWeekday.slice(1);
  const day = date.getDate();
  const month = new Intl.DateTimeFormat(locale, { month: "short" }).format(date);
  const year = date.getFullYear();
  return `${weekday} ${day} ${month} ${year}`;
}

export function formatDateTime(dateInput: string | Date, locale: string): string {
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput;
  const time = new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(date);
  return `${formatDate(date, locale)}, ${time}`;
}

// Formats a Date as the value a `datetime-local` input expects (no timezone).
export function toDatetimeLocalValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
