import React from 'react';

export function HubTabsNav({ tabs, activeTab, onChange }) {
  return (
    <nav
      className="z-10 rounded-2xl border border-zinc-800 bg-zinc-950/85 p-2 backdrop-blur-xl"
      data-testid="hub-tabs-nav"
      aria-label="AIMMH workspace tabs"
    >
      <div className="flex flex-nowrap gap-1" data-testid="hub-tabs-row-single-line">
        {tabs.map((tab) => {
          const active = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={`min-h-[2.5rem] min-w-0 flex-1 rounded-xl px-2 py-2 text-center text-[11px] leading-tight transition sm:text-xs ${active ? 'bg-emerald-600 text-white shadow-[0_8px_30px_rgba(16,185,129,0.25)]' : 'bg-zinc-950/40 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100'}`}
              data-testid={`hub-tab-${tab.id}`}
              aria-pressed={active}
            >
              <span className="block truncate" data-testid={`hub-tab-label-${tab.id}`}>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
