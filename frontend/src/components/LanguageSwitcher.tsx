import { useTranslation } from "react-i18next";
import { SUPPORTED_LANGUAGES, type Language } from "../i18n";
import { useAuth } from "../context/AuthContext";
import { useTopBarMenu } from "../context/TopBarMenuContext";

// Each language's own name, in that language — never translated, so it's
// always recognizable regardless of which language is currently active.
const NATIVE_NAMES: Record<Language, string> = {
  es: "Español",
  en: "English",
};

const FLAGS: Record<Language, string> = {
  es: "🇪🇸",
  en: "🇺🇸",
};

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const { user, updateProfile } = useAuth();
  const current = (i18n.resolvedLanguage ?? "es") as Language;
  const { open, containerRef, handleMouseEnter, handleMouseLeave, close, toggle } =
    useTopBarMenu("language");

  function selectLanguage(lng: Language) {
    close();
    i18n.changeLanguage(lng);
    // Keep it saved on the account so it follows the user to other devices,
    // and so backend-sent push notifications can be rendered in it too.
    if (user && user.language !== lng) {
      updateProfile({ language: lng });
    }
  }

  return (
    <div
      className="icon-menu language-switcher"
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        type="button"
        className="icon-menu-trigger language-switcher-trigger"
        onClick={toggle}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("language.label")}
      >
        <span aria-hidden="true">{FLAGS[current]}</span>
      </button>
      {open && (
        <div className="icon-menu-dropdown" role="menu">
          {SUPPORTED_LANGUAGES.map((lng) => (
            <button
              key={lng}
              type="button"
              role="menuitem"
              aria-current={lng === current}
              onClick={() => selectLanguage(lng)}
            >
              <span aria-hidden="true">{FLAGS[lng]}</span> {NATIVE_NAMES[lng]}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
