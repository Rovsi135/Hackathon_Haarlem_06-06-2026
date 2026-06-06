import { useCallback, useState } from "react";
import en from "../locales/en.json";
import nl from "../locales/nl.json";

const DICTS = { en, nl };

export const SUPPORTED_LANGS = ["en", "nl"];

const DEFAULT_LANG = (() => {
  const fromEnv = import.meta.env?.VITE_DEFAULT_LANG;
  return SUPPORTED_LANGS.includes(fromEnv) ? fromEnv : "en";
})();

/**
 * Substitute {placeholder} tokens in a translation string.
 * Localized copy never inlines values — they arrive via params.
 */
function interpolate(template, params) {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(params, key) ? String(params[key]) : match
  );
}

/**
 * useI18n — tiny, dependency-free localization hook.
 *
 * Returns:
 *   - lang:    current language code
 *   - setLang: switch language (re-renders consuming components)
 *   - t:       (key, params?) => localized string. Falls back to EN, then the key.
 */
export function useI18n() {
  const [lang, setLang] = useState(DEFAULT_LANG);

  const t = useCallback(
    (key, params) => {
      const dict = DICTS[lang] || DICTS.en;
      const value = dict[key] ?? DICTS.en[key] ?? key;
      return interpolate(value, params);
    },
    [lang]
  );

  return { lang, setLang, t };
}
