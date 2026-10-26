import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
import { Toaster } from './components/ui/sonner';
import AuthPage from './pages/AuthPage';
import AuthCallback from './pages/AuthCallback';
import AimmhHubPage from './pages/AimmhHubPage';
import SettingsPageV2 from './pages/SettingsPageV2';
import PricingPageV2 from './pages/PricingPageV2';
import HallOfMakersPage from './pages/HallOfMakersPage';
import AnalysisPage from './pages/AnalysisPage';
import ConsolePage from './pages/ConsolePage';
import './App.css';

class ErrorBoundary extends React.Component {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(err) { console.error('App error:', err); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-zinc-950 p-4" data-testid="error-boundary">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-6 space-y-3 max-w-md">
            <h1 className="text-base font-semibold text-zinc-200">Something went wrong</h1>
            <button
              onClick={() => { localStorage.clear(); window.location.href = '/chat'; }}
              className="w-full rounded-md bg-emerald-600 text-white h-10 text-sm hover:bg-emerald-500"
              data-testid="error-reset-btn"
            >
              Reset &amp; Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-zinc-950"><div className="text-zinc-500">Loading...</div></div>;
  return isAuthenticated ? children : <Navigate to="/auth" replace />;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-zinc-950"><div className="text-zinc-500">Loading...</div></div>;
  return !isAuthenticated ? children : <Navigate to="/chat" replace />;
};

function AppRoutes() {
  const location = useLocation();
  if (
    location.pathname === '/auth/callback'
    || location.pathname === '/auth/google'
    || location.hash?.includes('session_id=')
    || location.search?.includes('session_id=')
    || location.search?.includes('error=')
  ) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/auth" element={<PublicRoute><AuthPage /></PublicRoute>} />
      <Route path="/chat" element={<ProtectedRoute><AimmhHubPage /></ProtectedRoute>} />
      <Route path="/console" element={<ProtectedRoute><ConsolePage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPageV2 /></ProtectedRoute>} />
      <Route path="/pricing" element={<ProtectedRoute><PricingPageV2 /></ProtectedRoute>} />
      <Route path="/makers" element={<HallOfMakersPage />} />
      <Route path="/analysis" element={<ProtectedRoute><AnalysisPage /></ProtectedRoute>} />
      <Route path="/" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <ChatProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
          <Toaster position="top-right" theme="dark" />
        </BrowserRouter>
      </ChatProvider>
    </AuthProvider>
  );
}

export default App;
