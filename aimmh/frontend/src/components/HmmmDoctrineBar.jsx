import React from 'react';
import { useLocation } from 'react-router-dom';
import { useChat } from '../contexts/ChatContext';

export const HmmmDoctrineBar = () => {
  const location = useLocation();
  const { streaming, messages, selectedModels } = useChat();

  const latestAssistant = [...messages]
    .reverse()
    .find((msg) => msg.role === 'assistant' && msg.content)?.content;

  const doctrineState = streaming ? 'inference-active' : 'inference-idle';
  const doctrineSignal = latestAssistant
    ? latestAssistant.replace(/\s+/g, ' ').slice(0, 120)
    : 'awaiting fresh response signal';

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-border/70 bg-[#0D0F14]/95 backdrop-blur px-3 py-1.5"
      data-testid="hmmm-doctrine-bar"
    >
      <div className="mx-auto max-w-7xl flex items-center gap-2 text-[10px] sm:text-xs text-muted-foreground">
        <span className="font-semibold text-primary" data-testid="hmmm-doctrine-label">hmmm doctrine</span>
        <span className="opacity-60">·</span>
        <span data-testid="hmmm-doctrine-route">route:{location.pathname}</span>
        <span className="opacity-60">·</span>
        <span data-testid="hmmm-doctrine-state">state:{doctrineState}</span>
        <span className="opacity-60">·</span>
        <span data-testid="hmmm-doctrine-model-count">models:{selectedModels.length}</span>
        <span className="opacity-60">·</span>
        <span className="truncate" data-testid="hmmm-doctrine-signal">signal:{doctrineSignal}</span>
      </div>
    </div>
  );
};
