import { SUPPORTED_LANGS } from "../i18n/index.js";

/**
 * Sidebar — brand, navigation, language switch, run-cost meter and profile.
 * Background --mx-purple, padding S6, profile anchored to the bottom.
 */
export default function Sidebar({ t, lang, setLang, cost, user }) {
  const links = [
    { key: "nav.getting_started", icon: "◇", active: true },
    { key: "nav.support", icon: "☎" },
    { key: "nav.settings", icon: "⚙" },
  ];

  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="brand">
        <div className="brand-logo" aria-hidden="true">
          M
        </div>
        <div className="brand-title">{t("app.title")}</div>
      </div>

      <nav className="nav-links" aria-label="Sections">
        {links.map((link) => (
          <a
            key={link.key}
            className={`nav-link ${link.active ? "active" : ""}`}
            href="#"
            aria-current={link.active ? "page" : undefined}
          >
            <span className="nav-icon" aria-hidden="true">
              {link.icon}
            </span>
            {t(link.key)}
          </a>
        ))}
      </nav>

      {/* Run-cost meter — business case requirement #7 (cost-efficient generation) */}
      <div className="cost-meter" aria-live="polite">
        <span className="cm-label">{t("cost.label")}</span>
        <span className="cm-value">${cost.usd.toFixed(4)}</span>
        <span className="cm-sub">
          {t("cost.sub", { tokens: cost.tokens.toLocaleString(), model: cost.model })}
        </span>
      </div>

      {/* Bilingual output — business case requirement #8 */}
      <div className="lang-switch" role="group" aria-label="Language">
        {SUPPORTED_LANGS.map((code) => (
          <button
            key={code}
            type="button"
            className={`lang-option ${lang === code ? "active" : ""}`}
            aria-pressed={lang === code}
            onClick={() => setLang(code)}
          >
            {t(`lang.${code}`)}
          </button>
        ))}
      </div>

      <div className="profile">
        <div className="profile-avatar" aria-hidden="true">
          {user.initials}
        </div>
        <div>
          <div className="profile-name">{user.name}</div>
          <div className="profile-role">{t("profile.role")}</div>
        </div>
      </div>
    </aside>
  );
}
