import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import es from "./locales/es.json";

export const SUPPORTED_LANGUAGES = ["es", "en"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      es: { translation: es },
      en: { translation: en },
    },
    fallbackLng: "es",
    supportedLngs: SUPPORTED_LANGUAGES,
    detection: {
      // Only remember an explicit choice from the language switcher; never
      // infer from the browser, so the default is always Spanish.
      order: ["localStorage"],
      caches: ["localStorage"],
      lookupLocalStorage: "privento_language",
    },
    interpolation: { escapeValue: false },
  });

export default i18n;
