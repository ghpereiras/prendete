// Always renders day-month-year (e.g. "25 sep 2026"), regardless of the
// runtime locale's usual field order (some put month first, others day
// first) — that ambiguity is exactly what this format avoids.
export function formatDate(dateInput: string | Date, locale: string): string {
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput;
  const day = date.getDate();
  const month = new Intl.DateTimeFormat(locale, { month: "short" }).format(date);
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
}

export function formatDateTime(dateInput: string | Date, locale: string): string {
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput;
  const time = new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(date);
  return `${formatDate(date, locale)}, ${time}`;
}
