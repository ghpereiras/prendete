import { useTranslation } from "react-i18next";
import { SUPPORTED_LANGUAGES, type Language } from "../i18n";

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current = (i18n.resolvedLanguage ?? "es") as Language;

  return (
    <label className="language-switcher">
      <span className="sr-only">{t("language.label")}</span>
      <select
        value={current}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        aria-label={t("language.label")}
      >
        {SUPPORTED_LANGUAGES.map((lng) => (
          <option key={lng} value={lng}>
            {t(`language.${lng}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
