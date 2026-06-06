/**
 * Notes — speaker-notes area for the selected slide.
 * Renders the five Maverx facilitation fields, or a placeholder when no slide
 * is selected. (FRONTEND_L.md component 4; business case speaker-note fields.)
 */
export default function Notes({ notes, t }) {
  const fields = [
    ["aim", "notes.aim"],
    ["time", "notes.time"],
    ["instructions", "notes.instructions"],
    ["reflective_question", "notes.reflective_question"],
    ["debrief", "notes.debrief"],
  ];

  return (
    <div className="note-output" role="region" aria-label={t("notes.title")} aria-live="polite">
      <div className="note-header">
        <span className="note-title">🎤 {t("notes.title")}</span>
      </div>

      {notes ? (
        fields.map(([key, labelKey]) => (
          <div className="note-field" key={key}>
            <span className="nf-label">{t(labelKey)}</span>
            <span className="nf-value">{notes[key] || "—"}</span>
          </div>
        ))
      ) : (
        <p className="note-placeholder">{t("notes.placeholder")}</p>
      )}
    </div>
  );
}
