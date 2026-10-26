import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function ResponseMarkdown({ content, fontScale = 1 }) {
  return (
    <div className="prose prose-invert max-w-none prose-pre:overflow-x-auto prose-pre:rounded-2xl prose-pre:border prose-pre:border-zinc-800 prose-pre:bg-zinc-950 prose-code:text-emerald-300" style={{ fontSize: `${fontScale}rem`, lineHeight: 1.7 }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || ''}</ReactMarkdown>
    </div>
  );
}
