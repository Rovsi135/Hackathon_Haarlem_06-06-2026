/* ==========================================================================
   API client — switches between the deterministic mock and the real backend
   based on VITE_MOCK_API. Both expose the same method surface so the rest of
   the app never branches on environment.
   ========================================================================== */

import { mockApi } from "./mock.js";

const USE_MOCK = (import.meta.env?.VITE_MOCK_API ?? "true") !== "false";
const API_BASE = import.meta.env?.VITE_API_BASE ?? "/api";

async function post(path, body) {
  const isFormData = body instanceof FormData;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: isFormData ? undefined : { "Content-Type": "application/json" },
    body: isFormData ? body : JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

function buildFinalisePayload(payload) {
  const { styleGuideFiles = [], ...jsonPayload } = payload;
  if (!styleGuideFiles.length) return jsonPayload;

  const formData = new FormData();
  formData.append("payload", JSON.stringify(jsonPayload));
  styleGuideFiles.forEach((file) => {
    formData.append("style_guide_files", file, file.name);
  });
  return formData;
}

async function get(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Real backend adapter. The endpoint paths follow the events documented in
 * FRONTEND_L.md ("Behavior & State Machine"). Adjust paths here if the FastAPI
 * routes differ — this is the single integration point.
 */
const realApi = {
  validateIntake: (payload) => post("/validate-intake", payload),
  generateOutline: (payload) => post("/generate-outline", payload),
  proposeBlock: (payload) => post("/propose-block", payload),
  generateBlock: (payload) => post("/generate-block", payload),
  getBlockStatus: ({ job_id }) => get(`/block-status/${job_id}`),
  finalise: (payload) => post("/finalise", buildFinalisePayload(payload)),
  // The real backend should return cost in finalise / status responses; until
  // then we surface zeros so the meter renders without special-casing.
  getCost: () => ({ tokens: 0, usd: 0, model: "backend" }),
  resetCost: () => {},
};

export const api = USE_MOCK ? mockApi : realApi;
export const isMock = USE_MOCK;
