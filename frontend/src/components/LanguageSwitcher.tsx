import { useTranslation } from "react-i18next";
import { SUPPORTED_LANGUAGES, type Language } from "../i18n";

// Each language's own name, in that language — never translated, so it's
// always recognizable regardless of which language is currently active.
const NATIVE_NAMES: Record<Language, string> = {
  es: "Español",
  en: "English",
};

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current = (i18n.resolvedLanguage ?? "es") as Language;

  return (
    <label>
      <span className="sr-only">{t("language.label")}</span>
      <select
        value={current}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        aria-label={t("language.label")}
      >
        {SUPPORTED_LANGUAGES.map((lng) => (
          <option key={lng} value={lng}>
            {NATIVE_NAMES[lng]}
          </option>
        ))}
      </select>
    </label>
  );
}
