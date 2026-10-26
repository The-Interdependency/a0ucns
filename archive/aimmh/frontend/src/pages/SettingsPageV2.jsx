import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { KeyManager } from '../components/settings/KeyManager';
import { RegistryManager } from '../components/settings/RegistryManager';
import { ServiceAccountManager } from '../components/settings/ServiceAccountManager';

export default function SettingsPageV2() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('keys');

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200" data-testid="settings-page">
      <header className="flex items-center gap-3 border-b border-zinc-800 px-4 py-3">
        <button onClick={() => navigate('/chat')} className="rounded-lg p-2 hover:bg-zinc-900" data-testid="back-to-chat">
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">Settings</h1>
          <p className="text-xs text-zinc-500">Keys and registry management</p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <div className="mb-6 flex gap-2 border-b border-zinc-800">
          {[
            ['keys', 'API Keys'],
            ['registry', 'Model Registry'],
            ['service-accounts', 'Service Accounts'],
          ].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`border-b-2 px-4 py-3 text-sm transition ${tab === id ? 'border-zinc-200 text-zinc-100' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="space-y-4">
          {tab === 'keys' && <KeyManager />}
          {tab === 'registry' && <RegistryManager />}
          {tab === 'service-accounts' && <ServiceAccountManager />}
        </div>
      </main>
    </div>
  );
}
