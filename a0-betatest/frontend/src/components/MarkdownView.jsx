// === MODULE_BUILD ===
// id: fe_component_markdown_view
//   module_name: MarkdownView
//   module_kind: ui_component
//   summary: render Markdown + GFM tables + LaTeX (incl. arxiv \\(...\\) and \\[...\\] forms) via react-markdown + remark-math + rehype-katex
//   owner: Erin Spencer
//   public_surface: MarkdownView
//   internal_surface: none
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; chat replies render as plain text
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_component_markdown_view_boundaries
//   summary: pure renderer, no I/O
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_component_markdown_view
//   summary: pure renderer for markdown + math
//   exposes: MarkdownView
//   boundaries: auth:none, storage:none, network:none, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

/**
 * MarkdownView — renders Markdown + GFM tables + LaTeX/arXiv math.
 * Math is delimited by $...$ inline and $$...$$ block, plus \( \) and \[ \] for arxiv-style.
 */
export default function MarkdownView({ children }) {
  if (!children) return null;
  // Normalise common arxiv \( ... \) and \[ ... \] into $ and $$ so remark-math picks them up.
  let src = String(children);
  src = src
    .replace(/\\\((.+?)\\\)/gs, "$$$1$$")
    .replace(/\\\[(.+?)\\\]/gs, "$$$$$$1$$$$$$");

  return (
    <div className="prose-a0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
      >
        {src}
      </ReactMarkdown>
    </div>
  );
}
