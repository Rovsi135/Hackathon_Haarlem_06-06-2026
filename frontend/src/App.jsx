import { useEffect, useState } from "react";
import { useI18n } from "./i18n/index.js";
import { api } from "./api/client.js";
import Sidebar from "./components/Sidebar.jsx";
import Stage from "./components/Stage.jsx";
import AssistantPanel from "./components/AssistantPanel.jsx";

/* Intake question index → TrainingSpec field key (matches the backend agent). */
const ANSWER_KEYS = [
  "topic",
  "audience",
  "knowledge_level",
  "duration_minutes",
  "learning_objective",
];

/* The five didactic blocks, in fixed Maverx order. */
const BLOCK_ORDER = ["kickoff", "theory", "example", "exercise", "wrapup"];

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const USER = { name: "Ece Güngör", initials: "EG" };

/** Re-number slides sequentially across the whole deck. */
function withNumbers(slides) {
  return slides.map((s, i) => ({ ...s, slide_number: i + 1 }));
}

export default function App() {
  const { lang, setLang, t } = useI18n();

  // -- flow state ----------------------------------------------------------
  const [phase, setPhase] = useState("intake");
  const [step, setStep] = useState(0); // intake question index
  const [answers, setAnswers] = useState({});
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const [outline, setOutline] = useState([]);
  const [blocks, setBlocks] = useState({}); // { block_id: { status, slides } }
  const [currentBlockIndex, setCurrentBlockIndex] = useState(0);
  const [proposal, setProposal] = useState(null);
  const [proposalLoading, setProposalLoading] = useState(false);

  const [slides, setSlides] = useState([]);
  const [activeSlide, setActiveSlide] = useState(0);
  const [deckTitle, setDeckTitle] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");

  const [cost, setCost] = useState(() => api.getCost());
  const [busy, setBusy] = useState(false);

  // SlideKick's intro greeting (in the current language) on first mount.
  useEffect(() => {
    setMessages([{ role: "assistant", text: t("assistant.intro") }]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -- small helpers -------------------------------------------------------
  const addMessage = (role, text) => setMessages((m) => [...m, { role, text }]);
  const refreshCost = () => setCost(api.getCost());

  async function pollBlock(jobId) {
    for (let i = 0; i < 40; i++) {
      const status = await api.getBlockStatus({ job_id: jobId });
      refreshCost();
      if (status.done) return status;
      await delay(400);
    }
    throw new Error("Block generation timed out");
  }

  // -- intake --------------------------------------------------------------
  async function handleSend(value) {
    addMessage("user", value);
    setInput("");
    setBusy(true);
    try {
      const res = await api.validateIntake({ value, step, lang });
      refreshCost();
      if (!res.valid) {
        addMessage("assistant", res.followUp);
        return;
      }
      setAnswers((a) => ({ ...a, [ANSWER_KEYS[step]]: res.normalized }));
      if (step < ANSWER_KEYS.length - 1) {
        setStep(step + 1);
      } else {
        setPhase("outline_path");
        addMessage("assistant", t("phase.outline_path"));
      }
    } catch (err) {
      addMessage("error", String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  // -- outline -------------------------------------------------------------
  async function loadOutline() {
    setBusy(true);
    try {
      const { outline: nextOutline } = await api.generateOutline({ answers, lang });
      refreshCost();
      const blocksInit = {};
      nextOutline.forEach((b) => {
        blocksInit[b.block_id] = { status: "pending", slides: [] };
      });
      setOutline(nextOutline);
      setBlocks(blocksInit);
      setCurrentBlockIndex(0);
      setSlides([]);
      setPhase("outline_review");
    } finally {
      setBusy(false);
    }
  }

  async function handleChooseOutlinePath(pathId) {
    addMessage("user", t(`intake.option.${pathId}`));
    await loadOutline();
    addMessage("assistant", t("outline.subtitle"));
  }

  async function handleRegenerateOutline() {
    await loadOutline();
  }

  // -- block proposal + generation ----------------------------------------
  async function enterBlockProposal(idx) {
    setCurrentBlockIndex(idx);
    setProposal(null);
    setProposalLoading(true);
    setPhase("block_proposal");
    try {
      const { proposal: next } = await api.proposeBlock({ answers, outline, blockIndex: idx, lang });
      refreshCost();
      setProposal(next);
    } finally {
      setProposalLoading(false);
    }
  }

  async function handleApproveOutline() {
    addMessage("user", t("outline.approve"));
    await enterBlockProposal(0);
  }

  async function handleAdjustBlock() {
    addMessage("user", t("proposal.adjust"));
    await enterBlockProposal(currentBlockIndex);
  }

  async function handleApproveBlock() {
    const idx = currentBlockIndex;
    const block = outline[idx];
    addMessage("user", t("proposal.approve"));
    setBlocks((b) => ({ ...b, [block.block_id]: { ...b[block.block_id], status: "generating" } }));
    setPhase("block_generating");
    setBusy(true);
    try {
      const { job_id } = await api.generateBlock({ answers, outline, blockIndex: idx, lang });
      const status = await pollBlock(job_id);

      const firstNewIndex = slides.length;
      const merged = withNumbers([...slides, ...status.slides]);
      setSlides(merged);
      setActiveSlide(firstNewIndex);
      setBlocks((b) => ({ ...b, [block.block_id]: { status: "done", slides: status.slides } }));
      setProposal(null);

      if (idx < outline.length - 1) {
        setBusy(false);
        await enterBlockProposal(idx + 1);
      } else {
        setDeckTitle(`${answers.topic} — ${answers.audience}`);
        setActiveSlide(0); // open the review on slide 1
        setPhase("review");
        setBusy(false);
      }
    } catch (err) {
      addMessage("error", String(err.message || err));
      setBusy(false);
    }
  }

  // -- finalise ------------------------------------------------------------
  async function handleFinalise() {
    setBusy(true);
    try {
      const job_ids = outline.map((b) => blocks[b.block_id]);
      const { download_url, title } = await api.finalise({ answers, job_ids, lang });
      refreshCost();
      setDownloadUrl(download_url);
      setDeckTitle(title);
      setPhase("done");
    } catch (err) {
      addMessage("error", String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  function handleRestart() {
    api.resetCost();
    setPhase("intake");
    setStep(0);
    setAnswers({});
    setMessages([{ role: "assistant", text: t("assistant.intro") }]);
    setInput("");
    setOutline([]);
    setBlocks({});
    setCurrentBlockIndex(0);
    setProposal(null);
    setProposalLoading(false);
    setSlides([]);
    setActiveSlide(0);
    setDeckTitle("");
    setDownloadUrl("");
    setCost(api.getCost());
  }

  // -- progress dots -------------------------------------------------------
  const dots =
    phase === "intake"
      ? Array.from({ length: 5 }, (_, i) =>
          i < step ? "completed" : i === step ? "active" : "pending"
        )
      : BLOCK_ORDER.map((id, i) => {
          if (phase === "done" || blocks[id]?.status === "done") return "completed";
          if (
            i === currentBlockIndex &&
            (phase === "block_proposal" || phase === "block_generating")
          )
            return "active";
          return "pending";
        });

  const generatingBlockId = outline[currentBlockIndex]?.block_id;
  const generatingCount = outline[currentBlockIndex]?.slide_count_estimate || 0;

  return (
    <div className="app-shell" role="application">
      <Sidebar t={t} lang={lang} setLang={setLang} cost={cost} user={USER} />

      <div className="main-grid">
        <Stage
          phase={phase}
          t={t}
          lang={lang}
          outline={outline}
          blocks={blocks}
          currentBlockIndex={currentBlockIndex}
          slides={slides}
          activeSlide={activeSlide}
          setActiveSlide={setActiveSlide}
          deckTitle={deckTitle}
          generating={phase === "block_generating"}
          generatingBlockId={generatingBlockId}
          generatingCount={generatingCount}
          downloadUrl={downloadUrl}
          onDownload={() => {}}
          onRestart={handleRestart}
        />

        <AssistantPanel
          t={t}
          lang={lang}
          phase={phase}
          dots={dots}
          messages={messages}
          step={step}
          input={input}
          setInput={setInput}
          onSend={handleSend}
          onChooseOutlinePath={handleChooseOutlinePath}
          onApproveOutline={handleApproveOutline}
          onRegenerateOutline={handleRegenerateOutline}
          proposal={proposal}
          proposalLoading={proposalLoading}
          onApproveBlock={handleApproveBlock}
          onAdjustBlock={handleAdjustBlock}
          generatingBlockId={generatingBlockId}
          onFinalise={handleFinalise}
          currentBlockIndex={currentBlockIndex}
          outline={outline}
          busy={busy}
        />
      </div>
    </div>
  );
}
