/* ==========================================================================
   Deterministic in-browser mock API
   --------------------------------------------------------------------------
   Implements the state-machine contract from FRONTEND_L.md so the UI runs
   end-to-end without a backend (VITE_MOCK_API=true). The validation rules
   intentionally mirror the real intake agent (second_agent.py) so the demo
   behaves like the production flow.
   ========================================================================== */

const MOCK_MODEL = "claude-sonnet-4-6";

// --- helpers --------------------------------------------------------------

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Rough token accounting so the cost meter shows movement (business req #7).
// Mirrors OpenRouter's ~$3 / 1M input + $15 / 1M output pricing for Sonnet,
// blended to a single per-token figure for the demo.
const USD_PER_TOKEN = 9 / 1_000_000;

function estimateTokens(text) {
  if (!text) return 0;
  return Math.ceil(String(text).length / 4);
}

// The five didactic blocks, in fixed Maverx order.
const BLOCK_ORDER = ["kickoff", "theory", "example", "exercise", "wrapup"];
const BLOCK_WEIGHTS = {
  kickoff: 0.16,
  theory: 0.34,
  example: 0.16,
  exercise: 0.22,
  wrapup: 0.12,
};

// --- intake validation (mirrors second_agent.py) -------------------------

const VAGUE_TOPICS = new Set([
  "ai",
  "training",
  "business",
  "communication",
  "leadership",
  "management",
  "technology",
  "software",
  "data",
]);
const VAGUE_AUDIENCES = new Set([
  "everyone",
  "employees",
  "people",
  "staff",
  "team",
  "users",
  "workers",
  "students",
]);
const ACTION_VERBS = [
  "apply",
  "create",
  "build",
  "use",
  "evaluate",
  "improve",
  "write",
  "design",
  "explain",
  "analyze",
  "compare",
  "choose",
  "identify",
  "practice",
];

function normalizeKnowledgeLevel(answer) {
  const v = answer.trim().toLowerCase();
  if (["beginner", "beginners", "basic", "new", "none", "no experience"].includes(v))
    return "beginner";
  if (["intermediate", "some experience", "medium"].includes(v)) return "intermediate";
  if (["advanced", "expert", "experienced"].includes(v)) return "advanced";
  return null;
}

function parseDurationMinutes(answer) {
  const lowered = answer.trim().toLowerCase();
  const hourMatch = lowered.match(/(\d+(?:\.\d+)?)\s*(hours?|hrs?|h)\b/);
  const minuteMatch = lowered.match(/(\d+)\s*(minutes?|mins?|m)\b/);
  if (lowered.includes("half day") || lowered.includes("half-day")) return 240;
  if (lowered.includes("full day") || lowered.includes("full-day")) return 480;
  if (hourMatch) return Math.round(parseFloat(hourMatch[1]) * 60);
  if (minuteMatch) return parseInt(minuteMatch[1], 10);
  const bare = lowered.match(/^\s*(\d+)\s*$/);
  if (bare) return parseInt(bare[1], 10); // assume minutes
  return null;
}

/**
 * validateIntake(answers, step)
 *   step = index of the question being answered (0..4)
 *   returns { valid, normalized?, followUp? }
 */
async function validateIntake({ value, step }) {
  await delay(280);
  const answer = (value || "").trim();

  switch (step) {
    case 0: {
      // topic
      if (answer.length < 3)
        return { valid: false, followUp: "That's a bit short — name a concrete skill or domain." };
      if (VAGUE_TOPICS.has(answer.toLowerCase()))
        return {
          valid: false,
          followUp:
            "That's quite broad. What's the specific skill? For example: \"prompt engineering for marketing\".",
        };
      return { valid: true, normalized: answer };
    }
    case 1: {
      // target audience
      if (answer.length < 4)
        return { valid: false, followUp: "Who exactly is this for? Name a role, team or group." };
      if (VAGUE_AUDIENCES.has(answer.toLowerCase()))
        return {
          valid: false,
          followUp:
            "That's a little vague. Which team or role? For example: \"marketing team\" or \"HR managers\".",
        };
      return { valid: true, normalized: answer };
    }
    case 2: {
      // knowledge level
      const level = normalizeKnowledgeLevel(answer);
      if (!level)
        return {
          valid: false,
          followUp: "Please choose one of: beginner, intermediate, or advanced.",
        };
      return { valid: true, normalized: level };
    }
    case 3: {
      // duration
      const minutes = parseDurationMinutes(answer);
      if (minutes == null)
        return {
          valid: false,
          followUp: "How long is the session? For example: 90 minutes, 3 hours, or half day.",
        };
      if (minutes < 30)
        return { valid: false, followUp: "That seems short for a full training — try at least 30 minutes." };
      if (minutes > 480)
        return { valid: false, followUp: "For a single training, keep it under 8 hours." };
      return { valid: true, normalized: minutes };
    }
    case 4: {
      // learning objective
      const lowered = answer.toLowerCase();
      if (answer.split(/\s+/).length < 6)
        return {
          valid: false,
          followUp: "Make it a full outcome — \"By the end, participants can …\".",
        };
      if (!ACTION_VERBS.some((verb) => lowered.includes(verb)))
        return {
          valid: false,
          followUp:
            "Add a concrete action — what can participants do afterwards? (e.g. create, apply, evaluate).",
        };
      return { valid: true, normalized: answer };
    }
    default:
      return { valid: true, normalized: answer };
  }
}

// --- outline generation ---------------------------------------------------

function targetSlideCount(minutes) {
  // ~7 slides per hour, clamped to a sensible Tier-1 range.
  const raw = Math.round((minutes / 60) * 7);
  return Math.min(50, Math.max(12, raw));
}

function distributeSlides(total) {
  const counts = {};
  let assigned = 0;
  BLOCK_ORDER.forEach((id, i) => {
    if (i === BLOCK_ORDER.length - 1) {
      counts[id] = Math.max(2, total - assigned);
    } else {
      const n = Math.max(2, Math.round(total * BLOCK_WEIGHTS[id]));
      counts[id] = n;
      assigned += n;
    }
  });
  return counts;
}

const BLOCK_TITLES = {
  kickoff: "Opening / Kick-off",
  theory: "Theory",
  example: "Example",
  exercise: "Exercise",
  wrapup: "Wrap-up / Closing",
};

const BLOCK_DESCRIPTIONS = {
  kickoff: "Set learning goals, agenda and an energizer to open the session.",
  theory: "Core concepts explained clearly for the target audience.",
  example: "Concrete, recognizable illustrations of the theory in action.",
  exercise: "Active application — individual, pair or group work.",
  wrapup: "Key takeaways, link to practice and next steps.",
};

async function generateOutline({ answers }) {
  await delay(650);
  const minutes = Number(answers.duration_minutes) || 180;
  const total = targetSlideCount(minutes);
  const counts = distributeSlides(total);

  const outline = BLOCK_ORDER.map((id) => ({
    block_id: id,
    title: BLOCK_TITLES[id],
    description: BLOCK_DESCRIPTIONS[id],
    slide_count_estimate: counts[id],
    duration_min: Math.round(minutes * BLOCK_WEIGHTS[id]),
  }));

  return { outline };
}

// --- block proposal --------------------------------------------------------

function keyPointsFor(blockId, answers) {
  const topic = answers.topic || "the topic";
  const audience = answers.audience || "participants";
  const map = {
    kickoff: [
      `Why ${topic} matters for ${audience}`,
      "Learning goals and agenda",
      "Quick warm-up to surface prior experience",
    ],
    theory: [
      `Core principles of ${topic}`,
      "The mental model to remember",
      "Common pitfalls and how to avoid them",
    ],
    example: [
      `A real ${topic} scenario from ${audience}'s daily work`,
      "Walk-through of a good vs. weak approach",
      "What made the difference",
    ],
    exercise: [
      `Hands-on task applying ${topic}`,
      "Work in pairs, then compare results",
      "Group debrief on what worked",
    ],
    wrapup: [
      "Recap of the three things that must land",
      "Link to participants' real work",
      "Next steps and the post-bite assignment",
    ],
  };
  return map[blockId] || [];
}

async function proposeBlock({ answers, outline, blockIndex }) {
  await delay(420);
  const block = outline[blockIndex];
  const points = keyPointsFor(block.block_id, answers);
  return {
    proposal: {
      block_id: block.block_id,
      summary: `I'll create ${block.slide_count_estimate} slides for "${block.title}" covering ${points
        .map((p) => p.toLowerCase())
        .slice(0, 2)
        .join(", ")} and more.`,
      slide_count: block.slide_count_estimate,
      key_points: points,
    },
  };
}

// --- slide content generation ---------------------------------------------

const LAYOUT_BY_BLOCK = {
  kickoff: ["title_slide", "agenda", "content"],
  theory: ["content", "two_col", "content", "quote"],
  example: ["content", "two_col", "content"],
  exercise: ["exercise", "content", "exercise"],
  wrapup: ["content", "quote", "title_slide"],
};

// Deterministic pseudo-confidence: grounded blocks (kickoff/wrapup/exercise)
// score high; theory/example occasionally dip to demonstrate the review state.
function confidenceFor(blockId, indexInBlock) {
  const base = {
    kickoff: 0.95,
    theory: 0.86,
    example: 0.82,
    exercise: 0.93,
    wrapup: 0.96,
  }[blockId];
  // Make one mid-deck theory/example slide lower to exercise the UI states.
  const dip = (blockId === "theory" || blockId === "example") && indexInBlock === 1 ? 0.18 : 0;
  return Math.round(Math.max(0.55, base - dip) * 100) / 100;
}

function buildSlide(blockId, slideNumber, indexInBlock, slideCount, answers, blockDurationMin) {
  const topic = answers.topic || "the topic";
  const audience = answers.audience || "the team";
  const objective = answers.learning_objective || "apply the skill in their daily work";
  const layouts = LAYOUT_BY_BLOCK[blockId];
  const layout = layouts[indexInBlock % layouts.length];

  const templates = {
    kickoff: () => ({
      title: indexInBlock === 0 ? topic : indexInBlock === 1 ? "Today's agenda" : "What you already know",
      bullets:
        indexInBlock === 0
          ? [`A practical session for ${audience}`, `Goal: ${objective}`]
          : indexInBlock === 1
          ? ["Theory: the core ideas", "Worked example", "Hands-on exercise", "Wrap-up & next steps"]
          : ["Where have you used this before?", "What's one thing you find tricky?"],
    }),
    theory: () => ({
      title:
        indexInBlock === 0
          ? `What is ${topic}?`
          : `Key principle ${indexInBlock} of ${topic}`,
      bullets: [
        `A clear, ${audience}-friendly definition`,
        "Why it works the way it does",
        "A pitfall to watch out for",
      ],
    }),
    example: () => ({
      title: indexInBlock === 0 ? `${topic} in practice` : "Good vs. weak approach",
      bullets: [
        `A scenario ${audience} will recognize`,
        "Step-by-step walk-through",
        "What made the difference",
      ],
    }),
    exercise: () => ({
      title: `Exercise ${indexInBlock + 1}: try it yourself`,
      bullets: [
        `Apply ${topic} to a realistic task`,
        "Work in pairs (10 min)",
        "Compare results and discuss",
      ],
    }),
    wrapup: () => ({
      title: indexInBlock === 0 ? "Key takeaways" : indexInBlock === 1 ? "Make it stick" : "Thank you",
      bullets:
        indexInBlock === 0
          ? ["The three things that must land", `How this supports: ${objective}`]
          : indexInBlock === 1
          ? ["One change to try this week", "Your post-bite assignment"]
          : ["Questions?", "Resources to keep learning"],
    }),
  };

  const { title, bullets } = templates[blockId]();

  return {
    slide_number: slideNumber,
    layout,
    title,
    bullets,
    module_block: blockId,
    confidence: confidenceFor(blockId, indexInBlock),
    speaker_notes: {
      aim: `Help ${audience} grasp this part of ${topic}.`,
      time: `${Math.max(2, Math.round((Number(blockDurationMin) || 20) / slideCount))} min`,
      instructions:
        "Open with the question on the slide, let two or three people respond, then summarize before moving on.",
      reflective_question: bullets.slice(0, 3).join(" · "),
      debrief: "In one line: this is the part you'll actually use on Monday.",
    },
  };
}

// In-memory job store for block generation (simulates async rendering).
const jobs = new Map();
let jobCounter = 0;

async function generateBlock({ answers, outline, blockIndex }) {
  await delay(120);
  const block = outline[blockIndex];
  const jobId = `job_${++jobCounter}`;
  jobs.set(jobId, {
    answers,
    block,
    blockIndex,
    readyAt: Date.now() + 1400, // slides "ready" after a short delay
  });
  return { job_id: jobId };
}

async function getBlockStatus({ job_id }) {
  await delay(300);
  const job = jobs.get(job_id);
  if (!job) return { done: false, slides: [], slide_count: 0 };

  if (Date.now() < job.readyAt) {
    return { done: false, slides: [], slide_count: job.block.slide_count_estimate };
  }

  // Determine the starting slide number based on earlier blocks.
  let startNumber = 1;
  // Note: callers pass a running offset via job.block in real backends; here we
  // simply number within the deck using the block's position.
  const count = job.block.slide_count_estimate;
  const slides = [];
  for (let i = 0; i < count; i++) {
    slides.push(
      buildSlide(job.block.block_id, startNumber + i, i, count, job.answers, job.block.duration_min)
    );
  }
  jobs.delete(job_id);
  return { done: true, slides, slide_count: count };
}

// --- finalise --------------------------------------------------------------

async function finalise({ answers }) {
  await delay(900);
  const topic = answers.topic || "Training";
  const title = `${topic} — ${answers.audience || "Training"}`;
  // A real backend returns a signed URL to the generated bundle. For the mock
  // we return a data: URL placeholder so the download button is wired up.
  const url =
    "data:text/plain;charset=utf-8," +
    encodeURIComponent(
      `Maverx AI Training Builder\n\nThis is a mock download placeholder.\nIn the real app this is the generated .pptx bundle for:\n\n${title}\n`
    );
  return { download_url: url, title };
}

// --- cost accounting -------------------------------------------------------

let totalTokens = 0;

function chargeTokens(...texts) {
  const used = texts.reduce((sum, t) => sum + estimateTokens(t), 0);
  totalTokens += used;
  return used;
}

export function getMockCost() {
  return {
    tokens: totalTokens,
    usd: Math.round(totalTokens * USD_PER_TOKEN * 10000) / 10000,
    model: MOCK_MODEL,
  };
}

export function resetMockCost() {
  totalTokens = 0;
}

// --- exported mock client --------------------------------------------------

export const mockApi = {
  async validateIntake(payload) {
    chargeTokens(payload.value, "validate");
    return validateIntake(payload);
  },
  async generateOutline(payload) {
    chargeTokens(JSON.stringify(payload.answers), "outline".repeat(40));
    return generateOutline(payload);
  },
  async proposeBlock(payload) {
    chargeTokens(JSON.stringify(payload.answers), "proposal".repeat(20));
    return proposeBlock(payload);
  },
  async generateBlock(payload) {
    return generateBlock(payload);
  },
  async getBlockStatus(payload) {
    return getBlockStatus(payload);
  },
  async finalise(payload) {
    chargeTokens("finalise".repeat(30));
    return finalise(payload);
  },
  getCost: getMockCost,
  resetCost: resetMockCost,
};
