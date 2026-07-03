// === MODULE_BUILD ===
// id: fe_lib_api
//   module_name: api
//   module_kind: client
//   summary: axios-based REST client for every /api endpoint — health, BYOK keys, env vault, inventory, sessions, drafts, skill reports, fanout/daisy/synthesize chat, inspector, agents+slugs, instances CRUD, chat/instance, sentinels canon+modes+weights, overrides queue, gonals, usage
//   owner: Erin Spencer
//   public_surface: api
//   internal_surface: client
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; every page loses its data layer
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_lib_api_boundaries
//   summary: thin client over the REST surface; no caching, no I/O persistence
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_lib_api
//   summary: REST client surface for every /api endpoint
//   exposes: api
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===


import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// ─── Custom-keys vault (per-user, generic GitHub/GCP/AWS/etc.) ─────────────
export const customKeys = {
  list:    () => client.get("/custom-keys").then(r => r.data),
  upsert:  (body) => client.put("/custom-keys", body).then(r => r.data),
  reveal:  (id) => client.post(`/custom-keys/${id}/reveal`).then(r => r.data),
  remove:  (id) => client.delete(`/custom-keys/${id}`).then(r => r.data),
};

// ─── Demo quota ───────────────────────────────────────────────────────────
export const demoQuota = {
  get: () => client.get("/demo-quota").then(r => r.data),
};

// ─── Living spec ──────────────────────────────────────────────────────────
export const livingSpec = {
  get: () => client.get("/spec/living").then(r => r.data),
};

export const api = {
  base: API,
  health:           () => client.get("/health").then(r => r.data),

  // BYOK keys
  listKeys:         (user_id = "local") => client.get("/keys", { params: { user_id } }).then(r => r.data),
  upsertKey:        (body) => client.put("/keys", body).then(r => r.data),
  deleteKey:        (id, user_id = "local") => client.delete(`/keys/${id}`, { params: { user_id } }).then(r => r.data),

  // Vault (per-site multi-account env)
  listVault:        (user_id = "local") => client.get("/vault", { params: { user_id } }).then(r => r.data),
  upsertVault:      (body) => client.put("/vault", body).then(r => r.data),
  revealVault:      (body) => client.post("/vault/reveal", body).then(r => r.data),
  deleteVault:      (id, user_id = "local") => client.delete(`/vault/${id}`, { params: { user_id } }).then(r => r.data),

  // Inventory
  inventory:        (user_id = "local") => client.get("/models/inventory", { params: { user_id } }).then(r => r.data),

  // Sessions
  listSessions:     (user_id = "local") => client.get("/sessions", { params: { user_id } }).then(r => r.data),
  createSession:    (body) => client.post("/sessions", body).then(r => r.data),
  getSession:       (id, user_id = "local") => client.get(`/sessions/${id}`, { params: { user_id } }).then(r => r.data),
  updateSession:    (id, body) => client.patch(`/sessions/${id}`, body).then(r => r.data),
  deleteSession:    (id, user_id = "local") => client.delete(`/sessions/${id}`, { params: { user_id } }).then(r => r.data),

  // Drafts
  listDrafts:       (user_id = "local") => client.get("/drafts", { params: { user_id } }).then(r => r.data),
  createDraft:      (body) => client.post("/drafts", body).then(r => r.data),
  updateDraft:      (id, body) => client.patch(`/drafts/${id}`, body).then(r => r.data),
  deleteDraft:      (id, user_id = "local") => client.delete(`/drafts/${id}`, { params: { user_id } }).then(r => r.data),

  // msdmd skill coverage
  skillReport:        (block = "CAPABILITIES") => client.get("/skill/report", { params: { block } }).then(r => r.data),
  skillCapabilities:  () => client.get("/skill/capabilities/report").then(r => r.data),
  skillContracts:     () => client.get("/skill/contracts/report", { timeout: 60000 }).then(r => r.data),
  skillModuleBuild:   () => client.get("/skill/module-build/report").then(r => r.data),

  // Chat
  chatSingle:       (body) => client.post("/chat/single", body, { timeout: 180000 }).then(r => r.data),
  chatFanout:       (body) => client.post("/chat/fanout", body, { timeout: 300000 }).then(r => r.data),
  chatDaisy:        (body) => client.post("/chat/daisychain", body, { timeout: 300000 }).then(r => r.data),
  chatSynthesize:   (body) => client.post("/chat/synthesize", body, { timeout: 180000 }).then(r => r.data),

  // Inspector
  inspectorSnap:    () => client.get("/inspector/snapshot").then(r => r.data),
  inspectorBeat:    (intent) => client.post("/inspector/heartbeat", { intent }).then(r => r.data),

  // Agents (legacy skill manifest — kept for back-compat)
  listAgents:       () => client.get("/agents").then(r => r.data),
  createAgent:      (body) => client.post("/agents", body).then(r => r.data),
  agentManifest:    (slug) => client.get(`/agents/${slug}/manifest`).then(r => r.data),
  deleteAgent:      (slug) => client.delete(`/agents/${slug}`).then(r => r.data),

  // ─── Agent instances (canonical CRUD) ───────────────────────────────────
  listInstances:    (user_id = "local") => client.get("/instances", { params: { user_id } }).then(r => r.data),
  createInstance:   (body) => client.post("/instances", body).then(r => r.data),
  getInstance:      (id, user_id = "local") => client.get(`/instances/${id}`, { params: { user_id } }).then(r => r.data),
  patchInstance:    (id, body) => client.patch(`/instances/${id}`, body).then(r => r.data),
  deleteInstance:   (id, user_id = "local") => client.delete(`/instances/${id}`, { params: { user_id } }).then(r => r.data),
  archiveInstance:  (id, body) => client.post(`/instances/${id}/archive`, body).then(r => r.data),
  chatInstance:     (id, body) => client.post(`/chat/instance/${id}`, body, { timeout: 180000, validateStatus: (s) => s < 500 }).then(r => ({ status: r.status, data: r.data })),
  teacherContextPreview: (id, body) => client.post(`/instances/${id}/teacher-context-preview`, body).then(r => r.data),

  // ─── Tools (built-in + user webhook/MCP) ────────────────────────────────
  listTools:        () => client.get("/tools").then(r => r.data),

  // ─── Training Room (multi-teacher distillation) ─────────────────────────
  trainInstance:    (id, body) => client.post(`/instances/${id}/train`, body, { timeout: 300000 }).then(r => r.data),

  // ─── Sentinels (13-sentinel canon + per-agent modes/weights) ────────────
  sentinelsCanon:   () => client.get("/sentinels/canon").then(r => r.data),
  getSentinelModes: (agent_id, user_id = "local") => client.get(`/instances/${agent_id}/sentinel-modes`, { params: { user_id } }).then(r => r.data),
  patchSentinelModes: (agent_id, body) => client.patch(`/instances/${agent_id}/sentinel-modes`, body).then(r => r.data),
  bulkSentinelModes: (agent_id, body) => client.post(`/instances/${agent_id}/sentinel-modes/bulk`, body).then(r => r.data),
  getSentinelWeights: (agent_id, user_id = "local") => client.get(`/instances/${agent_id}/sentinel-weights`, { params: { user_id } }).then(r => r.data),
  patchSentinelWeights: (agent_id, body) => client.patch(`/instances/${agent_id}/sentinel-weights`, body).then(r => r.data),

  // ─── Overrides (async approve/reject for sentinel halts) ────────────────
  listOverrides:    (params = {}) => client.get("/overrides", { params }).then(r => r.data),
  getOverride:      (id) => client.get(`/overrides/${id}`).then(r => r.data),
  approveOverride:  (id, body) => client.post(`/overrides/${id}/approve`, body).then(r => r.data),
  rejectOverride:   (id, body) => client.post(`/overrides/${id}/reject`, body).then(r => r.data),
  expireOverrides:  () => client.post("/overrides/expire").then(r => r.data),

  // ─── Gonals (157-gonal carriers — public/mirror/private) ────────────────
  listGonals:       () => client.get("/gonals").then(r => r.data),

  // Usage
  usage:            (user_id = "local") => client.get("/usage", { params: { user_id } }).then(r => r.data),
};
