import Notes from "./Notes.jsx";
import ConfidenceBadge, { confidenceLevel } from "./ConfidenceBadge.jsx";

/* -- Hero (intake / outline-path phases) ---------------------------------- */
function Hero({ t }) {
  return (
    <section className="hero-card" role="region" aria-label="Slide viewer">
      <div className="hero-icon" aria-hidden="true">
        ✨
      </div>
      <h1 className="hero-title">{t("stage.title")}</h1>
      <p className="hero-text">{t("stage.subtitle")}</p>
    </section>
  );
}

/* -- Outline preview (outline-review / first block proposal) -------------- */
function OutlinePreview({ t, outline, currentBlockIndex, blocks }) {
  return (
    <section className="hero-card" role="region" aria-label={t("outline.title")} style={{ justifyContent: "flex-start", alignItems: "stretch", textAlign: "left" }}>
      <h2 className="deck-title">{t("outline.title")}</h2>
      <p className="hero-text" style={{ margin: 0 }}>
        {t("outline.subtitle")}
      </p>
      <div className="outline-list" style={{ marginTop: "var(--s3)" }}>
        {outline.map((block, i) => {
          const status = blocks[block.block_id]?.status || "pending";
          const isCurrent = i === currentBlockIndex && status !== "done";
          return (
            <div
              key={block.block_id}
              className={`outline-item ${status === "done" ? "done" : ""} ${isCurrent ? "current" : ""}`}
            >
              <span className="oi-index">{status === "done" ? "✓" : i + 1}</span>
              <div className="oi-body">
                <div className="oi-title">{t(`block.${block.block_id}`)}</div>
                <div className="oi-meta">
                  {block.description} · {t("outline.estimate", { count: block.slide_count_estimate })}
                </div>
              </div>
              <span className="oi-status">
                {status === "generating" ? t("phase.block_generating", { step: i + 1, total: outline.length }) : status}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* -- Single slide canvas -------------------------------------------------- */
function SlideCanvas({ slide, t }) {
  return (
    <div className="slide-canvas" role="img" aria-label={`Slide ${slide.slide_number}: ${slide.title}`}>
      <span className="slide-layout-tag">{slide.layout}</span>
      <span className="slide-kicker">{t(`block.${slide.module_block}`)}</span>
      <h2 className="slide-heading">{slide.title}</h2>
      <ul className="slide-bullets">
        {slide.bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
    </div>
  );
}

/* -- Generating placeholder ----------------------------------------------- */
function GeneratingCanvas({ t, blockId }) {
  return (
    <div className="slide-canvas" aria-busy="true" aria-label={t("generating.label", { block: t(`block.${blockId}`) })}>
      <div className="shimmer shimmer-line" style={{ width: "30%" }} />
      <div className="shimmer shimmer-line" style={{ width: "70%", height: "28px" }} />
      <div className="shimmer shimmer-line" style={{ width: "90%" }} />
      <div className="shimmer shimmer-line" style={{ width: "85%" }} />
      <div className="shimmer shimmer-line" style={{ width: "60%" }} />
    </div>
  );
}

/* -- Filmstrip thumbnails ------------------------------------------------- */
function Filmstrip({ slides, activeSlide, setActiveSlide, generatingCount }) {
  return (
    <div className="filmstrip" role="tablist" aria-label="Slides">
      {slides.map((slide, i) => (
        <button
          key={slide.slide_number}
          role="tab"
          aria-selected={i === activeSlide}
          className={`thumb ${i === activeSlide ? "active" : ""}`}
          onClick={() => setActiveSlide(i)}
        >
          <span
            className={`thumb-confidence ${confidenceLevel(slide.confidence)}`}
            style={{
              background:
                confidenceLevel(slide.confidence) === "high"
                  ? "var(--success)"
                  : confidenceLevel(slide.confidence) === "medium"
                  ? "var(--warning)"
                  : "var(--danger)",
            }}
            aria-hidden="true"
          />
          <span className="thumb-num">{slide.slide_number}</span>
          <span className="thumb-title">{slide.title}</span>
          <span className="thumb-block">{slide.module_block}</span>
        </button>
      ))}
      {Array.from({ length: generatingCount }).map((_, i) => (
        <div key={`gen-${i}`} className="thumb shimmer" aria-hidden="true" />
      ))}
    </div>
  );
}

/* -- Deck view (generation / review / done) ------------------------------- */
function DeckView({
  t,
  slides,
  activeSlide,
  setActiveSlide,
  deckTitle,
  generating,
  generatingBlockId,
  generatingCount,
}) {
  const active = slides[activeSlide];
  return (
    <>
      <div className="deck-header">
        <h2 className="deck-title">{deckTitle || t("review.title")}</h2>
        <span className="deck-meta">
          {slides.length} {slides.length === 1 ? "slide" : "slides"}
          {generating ? " · +" + generatingCount : ""}
        </span>
      </div>

      {active && (
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <ConfidenceBadge score={active.confidence} t={t} />
        </div>
      )}

      {generating && slides.length === 0 ? (
        <GeneratingCanvas t={t} blockId={generatingBlockId} />
      ) : active ? (
        <SlideCanvas slide={active} t={t} />
      ) : (
        <GeneratingCanvas t={t} blockId={generatingBlockId} />
      )}

      <Filmstrip
        slides={slides}
        activeSlide={activeSlide}
        setActiveSlide={setActiveSlide}
        generatingCount={generating ? generatingCount : 0}
      />

      <Notes notes={active ? active.speaker_notes : null} t={t} />
    </>
  );
}

/* -- Done card ------------------------------------------------------------ */
function DoneCard({ t, lang, deckTitle, downloadUrl, onDownload, onRestart }) {
  const items = [
    ["bundle.pptx", "📊"],
    ["bundle.prebite", "📄"],
    ["bundle.postbite", "📝"],
  ];
  return (
    <section className="hero-card" role="region" aria-label={t("done.title")}>
      <div className="hero-icon" aria-hidden="true">
        🎉
      </div>
      <h1 className="hero-title">{t("done.title")}</h1>
      <p className="hero-text">{t("done.subtitle", { lang: t(`lang.${lang}`) })}</p>
      <div className="bundle-list">
        {items.map(([key, icon]) => (
          <div className="bundle-item" key={key}>
            <span className="bi-icon" aria-hidden="true">
              {icon}
            </span>
            {t(key)}
          </div>
        ))}
      </div>
      <div className="button-row">
        <a
          className="primary-button"
          href={downloadUrl}
          download={`${(deckTitle || "maverx-training").replace(/[^\w-]+/g, "_")}.txt`}
          onClick={onDownload}
          style={{ textDecoration: "none" }}
        >
          ⬇ {t("done.download")}
        </a>
        <button type="button" className="ghost-button" onClick={onRestart}>
          {t("done.restart")}
        </button>
      </div>
    </section>
  );
}

/**
 * Stage — the left/main artifact area. Renders the right view for the phase.
 */
export default function Stage(props) {
  const { phase, slides } = props;

  if (phase === "intake" || phase === "outline_path") {
    return (
      <main className="stage">
        <Hero {...props} />
      </main>
    );
  }

  if (phase === "outline_review" || (phase === "block_proposal" && slides.length === 0)) {
    return (
      <main className="stage">
        <OutlinePreview {...props} />
      </main>
    );
  }

  if (phase === "done") {
    return (
      <main className="stage">
        <DoneCard {...props} />
      </main>
    );
  }

  // block_proposal (with slides), block_generating, review
  return (
    <main className="stage">
      <DeckView {...props} />
    </main>
  );
}
