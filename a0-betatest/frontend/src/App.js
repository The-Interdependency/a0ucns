// === MODULE_BUILD ===
// id: fe_app
//   module_name: App
//   module_kind: ui_root
//   summary: top-level router with AuthProvider — public routes (/, /login, /register, /spec) and protected routes (/workspace, /agents, /sentinels, /overrides, /inspector, /inventory, /keys, /custom-keys, /vault, /drafts)
//   owner: Erin Spencer
//   public_surface: App
//   internal_surface: none
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_app_boundaries
//   summary: routing shell + auth provider
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_app
//   summary: routing shell with auth gating
//   exposes: App
//   boundaries: auth:bearer, storage:none, network:none, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Shell from "./components/Shell";
import { AuthProvider, ProtectedRoute } from "./lib/auth";

import SplashPage from "./pages/SplashPage";
import LoginPage from "./pages/LoginPage";
import LivingSpecPage from "./pages/LivingSpecPage";

import WorkspacePage from "./pages/WorkspacePage";
import KeyVaultPage from "./pages/KeyVaultPage";
import CustomKeysPage from "./pages/CustomKeysPage";
import InventoryPage from "./pages/InventoryPage";
import VaultPage from "./pages/VaultPage";
import DraftsPage from "./pages/DraftsPage";
import InspectorPage from "./pages/InspectorPage";
import AgentsPage from "./pages/AgentsPage";
import TrainingRoom from "./pages/TrainingRoom";
import SentinelsPage from "./pages/SentinelsPage";
import OverridesPage from "./pages/OverridesPage";
import ToolsPage from "./pages/ToolsPage";
import MCPPage from "./pages/MCPPage";
import SkillsPage from "./pages/SkillsPage";

function Protected({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Shell>
          <Routes>
            {/* Public */}
            <Route path="/" element={<SplashPage />} />
            <Route path="/login" element={<LoginPage mode="login" />} />
            <Route path="/register" element={<LoginPage mode="register" />} />
            <Route path="/spec" element={<LivingSpecPage />} />

            {/* Protected */}
            <Route path="/workspace" element={<Protected><WorkspacePage /></Protected>} />
            <Route path="/agents" element={<Protected><AgentsPage /></Protected>} />
            <Route path="/training" element={<Protected><TrainingRoom /></Protected>} />
            <Route path="/sentinels" element={<Protected><SentinelsPage /></Protected>} />
            <Route path="/overrides" element={<Protected><OverridesPage /></Protected>} />
            <Route path="/tools" element={<Protected><ToolsPage /></Protected>} />
            <Route path="/mcp" element={<Protected><MCPPage /></Protected>} />
            <Route path="/skills" element={<Protected><SkillsPage /></Protected>} />
            <Route path="/inspector" element={<Protected><InspectorPage /></Protected>} />
            <Route path="/inventory" element={<Protected><InventoryPage /></Protected>} />
            <Route path="/keys" element={<Protected><KeyVaultPage /></Protected>} />
            <Route path="/custom-keys" element={<Protected><CustomKeysPage /></Protected>} />
            <Route path="/vault" element={<Protected><VaultPage /></Protected>} />
            <Route path="/drafts" element={<Protected><DraftsPage /></Protected>} />
          </Routes>
        </Shell>
      </AuthProvider>
    </BrowserRouter>
  );
}
