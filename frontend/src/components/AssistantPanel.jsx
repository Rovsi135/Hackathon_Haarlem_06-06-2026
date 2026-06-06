import { useEffect, useRef } from "react";
import ProgressDots from "./ProgressDots.jsx";

const INTAKE_TOTAL = 5;

/* Chips shown for specific intake questions. */
const TOPIC_CHIPS = [
  "chip.prompt_engineering",
  "chip.ai_literacy",
  "chip.ai_productivity",
  "chip.responsible_ai",
];
const LEVEL_CHIPS = [
  { key: "intake.level.beginner", value: "beginner" },
  { key: "intake.level.intermediate", value: "intermediate" },
  { key: "intake.level.advanced", value: "advanced" },
];

/* -- Conversation history ------------------------------------------------- */
function History({ messages, t }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [messages]);

  if (!messages.length) return null;
  return (
    <div className="history" ref={ref} aria-live="polite" aria-label={t("assistant.conversation")}>
      {messages.map((m, i) => {
        const text = m.key ? t(m.key, m.params) : m.text;
        return (
          <div key={i} className={`bubble ${m.role}`}>
            {text}
          </div>
        );
      })}
    </div>
  );
}

/* -- Intake question ------------------------------------------------------ */
function IntakeBlock({ t, step, input, setInput, onSend, onBack, busy }) {
  const chips =
    step === 0
      ? TOPIC_CHIPS.map((key) => ({ key, value: t(key) }))
      : step === 2
      ? LEVEL_CHIPS.map((c) => ({ key: c.key, value: c.value, label: t(c.key) }))
      : [];

  const submit = () => {
    const value = input.trim();
    if (!value || busy) return;
    onSend(value);
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <>
      <div className="question-block">
        <span className="question-badge">{step === 0 ? "AI" : `Q${step + 1}`}</span>
        <span className="question-title">{t(`intake.question.${step}.title`)}</span>
        <span className="question-help">{t(`intake.question.${step}.help`)}</span>
      </div>

      {chips.length > 0 && (
        <div className="chip-row">
          {chips.map((c) => (
            <button
              key={c.value}
              type="button"
              className="chip"
              disabled={busy}
              onClick={() => onSend(c.value, c.key)}
            >
              {c.label || c.value}
            </button>
          ))}
        </div>
      )}

      <div className="input-area">
        <textarea
          className="textarea-field"
          placeholder={t("intake.placeholder")}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          aria-label={t(`intake.question.${step}.title`)}
          disabled={busy}
        />
        <div className="action-row">
          {step > 0 && (
            <button type="button" className="ghost-button" onClick={onBack} disabled={busy}>
              {t("intake.back")}
            </button>
          )}
          <button type="button" className="primary-button" onClick={submit} disabled={busy || !input.trim()}>
            {t("intake.send")}
          </button>
        </div>
      </div>
    </>
  );
}

/* -- Outline path choice -------------------------------------------------- */
function OutlinePathBlock({ t, onChoose, busy }) {
  const options = [
    { id: "supply_outline", titleKey: "intake.option.supply_outline", descKey: "intake.option.supply_outline.desc" },
    { id: "ai_outline", titleKey: "intake.option.ai_outline", descKey: "intake.option.ai_outline.desc" },
  ];
  return (
    <div className="option-cards">
      {options.map((opt) => (
        <button
          key={opt.id}
          type="button"
          className="option-card"
          disabled={busy}
          onClick={() => onChoose(opt.id)}
        >
          <span className="opt-title">{t(opt.titleKey)}</span>
          <span className="opt-desc">{t(opt.descKey)}</span>
        </button>
      ))}
    </div>
  );
}

/* -- Outline review controls ---------------------------------------------- */
function OutlineReviewBlock({ t, onApprove, onRegenerate, busy }) {
  return (
    <>
      <div className="question-block">
        <span className="question-title">{t("outline.title")}</span>
        <span className="question-help">{t("outline.subtitle")}</span>
      </div>
      <div className="button-row">
        <button type="button" className="primary-button" onClick={onApprove} disabled={busy}>
          {t("outline.approve")}
        </button>
        <button type="button" className="ghost-button" onClick={onRegenerate} disabled={busy}>
          {t("outline.regenerate")}
        </button>
      </div>
    </>
  );
}

/* -- Block proposal ------------------------------------------------------- */
function ProposalBlock({ t, proposal, loading, onApprove, onAdjust, busy }) {
  if (loading || !proposal) {
    return (
      <div className="question-block" aria-busy="true">
        <div className="shimmer shimmer-line" style={{ width: "60%" }} />
        <div className="shimmer shimmer-line" style={{ width: "90%" }} />
        <div className="shimmer shimmer-line" style={{ width: "80%" }} />
      </div>
    );
  }
  return (
    <>
      <div className="question-block">
        <span className="question-badge">{t("proposal.slides", { count: proposal.slide_count })}</span>
        <span className="question-title">{t("proposal.title")}</span>
        <span className="question-help">{proposal.summary}</span>
      </div>
      <div className="note-field">
        <span className="nf-label">{t("proposal.keypoints")}</span>
        <ul className="slide-bullets" style={{ paddingLeft: "var(--s4)" }}>
          {proposal.key_points.map((p, i) => (
            <li key={i} style={{ fontSize: "14px" }}>
              {p}
            </li>
          ))}
        </ul>
      </div>
      <div className="button-row">
        <button type="button" className="primary-button" onClick={onApprove} disabled={busy}>
          {t("proposal.approve")}
        </button>
        <button type="button" className="ghost-button" onClick={onAdjust} disabled={busy}>
          {t("proposal.adjust")}
        </button>
      </div>
    </>
  );
}

/* -- Generating ----------------------------------------------------------- */
function GeneratingBlock({ t, blockId }) {
  return (
    <div className="question-block" aria-busy="true" aria-live="polite">
      <span className="question-title">{t("generating.label", { block: t(`block.${blockId}`) })}</span>
      <div className="shimmer shimmer-line" style={{ width: "100%" }} />
      <div className="shimmer shimmer-line" style={{ width: "85%" }} />
    </div>
  );
}

/* -- Review (finalise) ---------------------------------------------------- */
function ReviewBlock({ t, onFinalise, busy }) {
  return (
    <>
      <div className="question-block">
        <span className="question-title">{t("review.title")}</span>
        <span className="question-help">{t("review.subtitle")}</span>
      </div>
      <button type="button" className="primary-button" onClick={onFinalise} disabled={busy}>
        {t("action.generate_deck")}
      </button>
    </>
  );
}

/**
 * AssistantPanel — right-column conversation + controls.
 * Renders the correct control block for the current phase and always shows the
 * progress dots and conversation history above it.
 */
export default function AssistantPanel(props) {
  const { t, phase, dots, messages } = props;

  const phaseLabel = (() => {
    switch (phase) {
      case "intake":
        return t("phase.intake", { step: props.step + 1, total: INTAKE_TOTAL });
      case "block_proposal":
        return t("phase.block_proposal", { step: props.currentBlockIndex + 1, total: props.outline.length });
      case "block_generating":
        return t("phase.block_generating", {
          step: props.currentBlockIndex + 1,
          total: props.outline.length,
        });
      default:
        return t(`phase.${phase}`);
    }
  })();

  return (
    <section className="assistant-panel" role="complementary" aria-label={t("assistant.aria")}>
      <header className="panel-header">
        <div className="assistant-id">
          <div className="assistant-avatar" aria-hidden="true">
            🤖
          </div>
          <div>
            <div className="assistant-name">{t("assistant.name")}</div>
            <div className="phase-label">{phaseLabel}</div>
          </div>
        </div>
        <ProgressDots states={dots} />
      </header>

      <History messages={messages} t={t} />

      {phase === "intake" && (
        <IntakeBlock
          t={t}
          step={props.step}
          input={props.input}
          setInput={props.setInput}
          onSend={props.onSend}
          onBack={props.onBack}
          busy={props.busy}
        />
      )}

      {phase === "outline_path" && <OutlinePathBlock t={t} onChoose={props.onChooseOutlinePath} busy={props.busy} />}

      {phase === "outline_review" && (
        <OutlineReviewBlock
          t={t}
          onApprove={props.onApproveOutline}
          onRegenerate={props.onRegenerateOutline}
          busy={props.busy}
        />
      )}

      {phase === "block_proposal" && (
        <ProposalBlock
          t={t}
          proposal={props.proposal}
          loading={props.proposalLoading}
          onApprove={props.onApproveBlock}
          onAdjust={props.onAdjustBlock}
          busy={props.busy}
        />
      )}

      {phase === "block_generating" && <GeneratingBlock t={t} blockId={props.generatingBlockId} />}

      {phase === "review" && <ReviewBlock t={t} onFinalise={props.onFinalise} busy={props.busy} />}

      {phase === "done" && (
        <div className="question-block">
          <span className="question-title">{t("done.title")}</span>
          <span className="question-help">{t("done.subtitle", { lang: t(`lang.${props.lang}`) })}</span>
        </div>
      )}
    </section>
  );
}
