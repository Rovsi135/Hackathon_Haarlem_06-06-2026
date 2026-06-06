import { SUPPORTED_LANGS } from "../i18n/index.js";

/**
 * Sidebar: brand, lower-left navigation, language switch, run-cost meter and profile.
 */
export default function Sidebar({ t, lang, setLang, cost, user }) {
  const profile = { ...user, name: "Lucas van Zuiddam", initials: "LV" };
  const links = [
    { key: "nav.getting_started", icon: "chat", active: true },
    { key: "nav.support", icon: "help" },
    { key: "nav.settings", icon: "settings" },
  ];

  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="brand">
        <div className="brand-symbol" aria-hidden="true">
          <span className="brand-bar brand-bar-purple" />
          <span className="brand-bar brand-bar-pink" />
          <span className="brand-bar brand-bar-orange" />
        </div>
        <div>
          <div className="brand-wordmark">maverx</div>
          <div className="brand-subtitle">{t("AI Training Builder")}</div>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-actions">
          <div className="cost-meter" aria-live="polite">
            <span className="cm-label">{t("cost.label")}</span>
            <span className="cm-value">${cost.usd.toFixed(4)}</span>
            <span className="cm-sub">
              {t("cost.sub", { tokens: cost.tokens.toLocaleString(), model: cost.model })}
            </span>
          </div>

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
        </div>

        <nav className="nav-links" aria-label="Sections">
          {links.map((link) => (
            <a
              key={link.key}
              className={`nav-link ${link.active ? "active" : ""}`}
              href="#"
              aria-current={link.active ? "page" : undefined}
            >
              <span className={`nav-icon nav-icon-${link.icon}`} aria-hidden="true" />
              {t(link.key)}
            </a>
          ))}
        </nav>

        <div className="profile">
          <div className="profile-avatar" aria-hidden="true">
            {profile.initials}
          </div>
          <div className="profile-copy">
            <div className="profile-name">{profile.name}</div>
          </div>
          <button className="logout-button" type="button" aria-label="Sign out" />
        </div>
      </div>
    </aside>
  );
}
