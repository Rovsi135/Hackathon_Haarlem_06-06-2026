import { useRef, useState } from "react";
import { SUPPORTED_LANGS } from "../i18n/index.js";

/**
 * Sidebar: brand, lower-left navigation, language switch, run-cost meter and profile.
 */
export default function Sidebar({ t, lang, setLang, cost, user }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);
  const profile = { ...user, name: "Lucas van Zuiddam", initials: "LV" };
  const links = [
    { key: "nav.getting_started", icon: "chat", active: true },
    { key: "nav.support", icon: "help" },
    { key: "nav.settings", icon: "settings" },
  ];

  const acceptedExtensions = [".pdf", ".pptx"];

  function pickFiles(nextFiles) {
    const allowed = Array.from(nextFiles).filter((file) =>
      acceptedExtensions.some((extension) => file.name.toLowerCase().endsWith(extension))
    );
    setFiles((current) => {
      const known = new Set(current.map((file) => `${file.name}-${file.size}`));
      return [
        ...current,
        ...allowed.filter((file) => !known.has(`${file.name}-${file.size}`)),
      ];
    });
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    pickFiles(event.dataTransfer.files);
  }

  function closeSettingsModal() {
    setSettingsOpen(false);
    setIsDragging(false);
  }

  function formatFileSize(size) {
    if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <aside className="sidebar" role="navigation" aria-label={t("nav.aria")}>
      <div className="brand">
        <div className="brand-symbol" aria-hidden="true">
          <span className="brand-bar brand-bar-purple" />
          <span className="brand-bar brand-bar-pink" />
          <span className="brand-bar brand-bar-orange" />
        </div>
        <div>
          <div className="brand-wordmark">maverx</div>
          <div className="brand-subtitle">{t("app.subtitle")}</div>
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

          <div className="lang-switch" role="group" aria-label={t("language.aria")}>
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

        <nav className="nav-links" aria-label={t("sections.aria")}>
          {links.map((link) => (
            <div
              key={link.key}
              className={`nav-link-wrap ${link.icon === "settings" ? "settings-wrap" : ""}`}
            >
              {link.icon === "settings" ? (
                <>
                  <button
                    className={`nav-link nav-link-button ${settingsOpen ? "active" : ""}`}
                    type="button"
                    aria-expanded={settingsOpen}
                    aria-controls="settings-upload-modal"
                    onClick={() => setSettingsOpen(true)}
                  >
                    <span className={`nav-icon nav-icon-${link.icon}`} aria-hidden="true" />
                    {t(link.key)}
                  </button>

                  {settingsOpen && (
                    <div
                      className="settings-modal-backdrop"
                      role="presentation"
                      onMouseDown={closeSettingsModal}
                    >
                      <div
                        id="settings-upload-modal"
                        className="settings-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="settings-upload-title"
                        onMouseDown={(event) => event.stopPropagation()}
                      >
                        <div className="settings-modal-header">
                          <div>
                            <h2 id="settings-upload-title" className="settings-modal-title">
                              Upload source files
                            </h2>
                            <p className="settings-modal-subtitle">Add PDF or PPTX files.</p>
                          </div>
                          <button
                            className="modal-close-button"
                            type="button"
                            aria-label="Close settings"
                            onClick={closeSettingsModal}
                          />
                        </div>

                        <div
                          className={`drop-zone ${isDragging ? "dragging" : ""}`}
                          onDragOver={(event) => {
                            event.preventDefault();
                            setIsDragging(true);
                          }}
                          onDragLeave={() => setIsDragging(false)}
                          onDrop={handleDrop}
                        >
                          <span className="drop-icon" aria-hidden="true" />
                          <span className="drop-title">Drop files here</span>
                          <span className="drop-help">PDF or PPTX</span>
                        </div>

                        <button
                          className="upload-button"
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                        >
                          Upload files
                        </button>

                        <input
                          ref={fileInputRef}
                          className="file-input"
                          type="file"
                          accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation"
                          multiple
                          onChange={(event) => {
                            pickFiles(event.target.files);
                            event.target.value = "";
                          }}
                        />

                        {files.length > 0 && (
                          <div className="uploaded-files" aria-live="polite">
                            {files.map((file) => (
                              <div className="uploaded-file" key={`${file.name}-${file.size}`}>
                                <span className="uploaded-file-name">{file.name}</span>
                                <span className="uploaded-file-size">{formatFileSize(file.size)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <a
                  className={`nav-link ${link.active ? "active" : ""}`}
                  href="#"
                  aria-current={link.active ? "page" : undefined}
                >
                  <span className={`nav-icon nav-icon-${link.icon}`} aria-hidden="true" />
                  {t(link.key)}
                </a>
              )}
            </div>
          ))}
        </nav>

        <div className="profile">
          <div className="profile-avatar" aria-hidden="true">
            {profile.initials}
          </div>
          <div className="profile-copy">
            <div className="profile-name">{profile.name}</div>
          </div>
          <button className="logout-button" type="button" aria-label={t("profile.sign_out")} />
        </div>
      </div>
    </aside>
  );
}
