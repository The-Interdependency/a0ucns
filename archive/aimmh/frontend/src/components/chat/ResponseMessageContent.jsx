import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const formatJsonForDisplay = (raw = '') => {
  const trimmed = String(raw || '').trim();
  if (!trimmed || (!trimmed.startsWith('{') && !trimmed.startsWith('['))) {
    return null;
  }

  try {
    return JSON.stringify(JSON.parse(trimmed), null, 2);
  } catch {
    return null;
  }
};

const normalizeContentForDisplay = (raw) => {
  if (typeof raw === 'string') return raw;
  if (raw === null || raw === undefined) return '';
  if (typeof raw === 'object') {
    try {
      return JSON.stringify(raw, null, 2);
    } catch {
      return String(raw);
    }
  }
  return String(raw);
};

export const ResponseMessageContent = ({ content = '', messageId, streaming = false, renderMode = 'markdown' }) => {
  const normalizedContent = normalizeContentForDisplay(content);
  const safeMessageId = typeof messageId === 'string' || typeof messageId === 'number' ? messageId : 'unknown';
  const prettyJson = renderMode === 'native' ? null : formatJsonForDisplay(normalizedContent);

  return (
    <div className="prose prose-invert max-w-none text-sm leading-relaxed break-words" data-testid={`message-content-${safeMessageId}`}>
      {renderMode === 'native' ? (
        <div className="space-y-1" data-testid={`message-format-native-wrap-${safeMessageId}`}>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground" data-testid={`message-format-native-badge-${safeMessageId}`}>
            Native text
          </div>
          <pre className="rounded-md bg-black/40 p-3 overflow-x-auto my-1">
            <code className="font-mono text-xs whitespace-pre-wrap break-words">{normalizedContent}</code>
          </pre>
        </div>
      ) : prettyJson ? (
        <div className="space-y-1">
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground" data-testid={`message-format-json-badge-${safeMessageId}`}>
            JSON
          </div>
          <pre className="rounded-md bg-black/40 p-3 overflow-x-auto my-1">
            <code className="font-mono text-xs whitespace-pre-wrap">{prettyJson}</code>
          </pre>
        </div>
      ) : (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p className="my-2 leading-relaxed">{children}</p>,
            code: ({ inline, className, children, ...props }) =>
              inline ? (
                <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs" {...props}>{children}</code>
              ) : (
                <pre className="rounded-md bg-black/40 p-3 overflow-x-auto my-2">
                  <code className={`font-mono text-xs ${className || ''}`} {...props}>{children}</code>
                </pre>
              ),
            table: ({ children }) => <table className="w-full border-collapse text-xs my-2">{children}</table>,
            th: ({ children }) => <th className="border border-border px-2 py-1 text-left">{children}</th>,
            td: ({ children }) => <td className="border border-border px-2 py-1 align-top">{children}</td>,
            ul: ({ children }) => <ul className="list-disc pl-5 my-2">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-5 my-2">{children}</ol>,
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noreferrer" className="text-cyan-300 underline break-all">{children}</a>
            )
          }}
        >
          {normalizedContent}
        </ReactMarkdown>
      )}
      {streaming && <span className="streaming-cursor" />}
    </div>
  );
};
