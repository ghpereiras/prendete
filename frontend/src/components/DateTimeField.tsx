import { useRef, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { formatDateTime } from "../utils/date";

const supportsShowPicker =
  typeof HTMLInputElement !== "undefined" && "showPicker" in HTMLInputElement.prototype;

interface DateTimeFieldProps {
  value: string;
  onChange: (value: string) => void;
  min?: string;
}

// Forces picking the date/time through the native picker instead of typing it
// into the day/month/year/hour sub-fields. The real <input> is kept invisible
// (opacity: 0) and a separate span shows the formatted value instead — if the
// real input were visible, clicking it would highlight whichever sub-field
// the browser focuses, which looks like a stray text selection to the user.
// Falls back to a normal visible, editable field on browsers without
// showPicker() so it never becomes unusable.
export default function DateTimeField({ value, onChange, min }: DateTimeFieldProps) {
  const { i18n } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);

  if (!supportsShowPicker) {
    return (
      <input
        type="datetime-local"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
      />
    );
  }

  // Blocks typing into the day/month/year/hour sub-fields, but Enter/Space
  // still open the picker so the field stays reachable without a mouse.
  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Tab") return;
    e.preventDefault();
    if (e.key === "Enter" || e.key === " ") inputRef.current?.showPicker();
  }

  return (
    <div className="datetime-field">
      <span className={value ? undefined : "datetime-field-placeholder"}>
        {value ? formatDateTime(value, i18n.resolvedLanguage ?? "es") : "--/--/----, --:--"}
      </span>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M3 9h18M8 3v4M16 3v4" />
      </svg>
      <input
        ref={inputRef}
        type="datetime-local"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onClick={() => inputRef.current?.showPicker()}
        onKeyDown={handleKeyDown}
        min={min}
      />
    </div>
  );
}
