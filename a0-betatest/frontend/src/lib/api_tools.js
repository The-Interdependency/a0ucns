// === MODULE_BUILD ===
// id: fe_lib_api_tools
//   module_name: api_tools
//   module_kind: client
//   summary: axios client for the tools / mcp servers / skills REST surface — list/register/invoke tools, MCP server CRUD with refresh, skills CRUD with overlap check, skill-lib sync, MCP publish token
//   owner: Erin Spencer
//   public_surface: toolsApi, mcpClientApi, mcpPublishApi, skillsApi
//   internal_surface: client
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; tools/mcp/skills pages lose their data layer
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_lib_api_tools_boundaries
//   summary: REST client for the new layer
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_lib_api_tools
//   summary: tools/mcp/skills client
//   exposes: toolsApi, mcpClientApi, mcpPublishApi, skillsApi
//   boundaries: auth:bearer, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import axios from "axios";

const client = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  withCredentials: true,
  timeout: 60000,
});

export const toolsApi = {
  list:    () => client.get("/tools").then(r => r.data),
  registerWebhook: (body) => client.post("/tools/webhook", body).then(r => r.data),
  remove:  (name) => client.delete(`/tools/${encodeURIComponent(name)}`).then(r => r.data),
  invoke:  (name, body) => client.post(`/tools/${encodeURIComponent(name)}/invoke`, body, { validateStatus: s => s < 500 }).then(r => ({ status: r.status, data: r.data })),
};

export const mcpClientApi = {
  list:    () => client.get("/mcp/servers").then(r => r.data),
  add:     (body) => client.post("/mcp/servers", body).then(r => r.data),
  refresh: (id) => client.post(`/mcp/servers/${id}/refresh`).then(r => r.data),
  remove:  (id) => client.delete(`/mcp/servers/${id}`).then(r => r.data),
};

export const mcpPublishApi = {
  getToken: () => client.get("/mcp/publish-token").then(r => r.data),
  rotate:   () => client.post("/mcp/publish-token/rotate").then(r => r.data),
};

export const skillsApi = {
  list:     () => client.get("/skills").then(r => r.data),
  checkOverlap: (body) => client.post("/skills/check-overlap", body).then(r => r.data),
  register: (body) => client.post("/skills", body, { validateStatus: s => s < 500 }).then(r => ({ status: r.status, data: r.data })),
  remove:   (id) => client.delete(`/skills/${id}`).then(r => r.data),
  sync:     () => client.post("/skills/sync").then(r => r.data),
};
