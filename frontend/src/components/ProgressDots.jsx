/**
 * ProgressDots — 5 horizontal dots (FRONTEND_L.md "Exact progress dots").
 * Props:
 *   states: array of "completed" | "active" | "pending" (length 5)
 */
export default function ProgressDots({ states }) {
  return (
    <div className="progress-dots" role="progressbar" aria-label="Progress">
      {states.map((state, i) => (
        <span key={i} className={`dot ${state}`} aria-hidden="true" />
      ))}
    </div>
  );
}
