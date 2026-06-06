/**
 * ConfidenceBadge — per-slide reliability indicator (business case req #6).
 * Maps a 0..1 confidence score to one of three calibrated bands so the
 * trainer knows which slides need a closer look before presenting.
 */

export function confidenceLevel(score) {
  if (score >= 0.85) return "high";
  if (score >= 0.7) return "medium";
  return "low";
}

export default function ConfidenceBadge({ score, t }) {
  const level = confidenceLevel(score);
  const labelKey = `confidence.${level}`;
  return (
    <span
      className={`confidence-badge ${level}`}
      title={`${t("confidence.label")}: ${Math.round(score * 100)}%`}
      aria-label={`${t("confidence.label")}: ${Math.round(score * 100)}%, ${t(labelKey)}`}
    >
      <span className="cb-dot" aria-hidden="true" />
      {Math.round(score * 100)}% · {t(labelKey)}
    </span>
  );
}
