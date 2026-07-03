// === MODULE_BUILD ===
// id: fe_page_splash
//   module_name: SplashPage
//   module_kind: ui_page
//   summary: public landing — "changes constant. refinements welcome." manifesto + Sign in / Sign up CTAs + email-of-record (wayseer@interdependentway.org); shows demo-mode notice for unauthenticated visitors
//   owner: Erin Spencer
//   public_surface: SplashPage
//   internal_surface: none
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; '/' renders the Workspace directly
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_splash_boundaries
//   summary: presentational landing page
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_splash
//   summary: public landing page
//   exposes: SplashPage
//   boundaries: auth:none, storage:none, network:external, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, GithubLogo, GoogleLogo, ShieldCheck, Lightning } from "@phosphor-icons/react";

export default function SplashPage() {
  return (
    <div className="min-h-[80vh] flex flex-col" data-testid="page-splash">
      <section className="flex-1 grid lg:grid-cols-[1.2fr_0.8fr] gap-12 items-start py-12 lg:py-20">
        <div className="space-y-8">
          <div className="flex items-center gap-3">
            <span className="block h-px w-12 bg-accent-cyan/60" />
            <span className="font-mono text-xs uppercase tracking-ultra text-accent-cyan/80" data-testid="splash-eyebrow">
              a0p · interdependent way
            </span>
          </div>

          <h1 className="text-5xl lg:text-7xl font-mono leading-tight tracking-tight text-white">
            changes constant.<br />
            <span className="text-accent-cyan">refinements welcome.</span>
          </h1>

          <p className="text-base text-neutral-300 max-w-xl font-mono leading-relaxed">
            A BYOK research instrument for many minds at once.
            Three trainable cores. Thirteen sentinels. One canon —
            built to be inspected, halted, and corrected.
          </p>

          <div className="flex flex-wrap gap-3 pt-2" data-testid="splash-cta-row">
            <Link
              to="/login"
              data-testid="splash-signin-btn"
              className="inline-flex items-center gap-2 px-5 py-3 border border-accent-cyan/60 text-accent-cyan font-mono text-sm uppercase tracking-wider hover:bg-accent-cyan/10 transition-colors"
            >
              sign in <ArrowRight size={14} />
            </Link>
            <Link
              to="/register"
              data-testid="splash-signup-btn"
              className="inline-flex items-center gap-2 px-5 py-3 border border-white/20 text-white font-mono text-sm uppercase tracking-wider hover:bg-white/5 transition-colors"
            >
              create account
            </Link>
            <Link
              to="/spec"
              data-testid="splash-spec-link"
              className="inline-flex items-center gap-2 px-5 py-3 text-neutral-400 font-mono text-sm uppercase tracking-wider hover:text-white transition-colors"
            >
              read the living spec
            </Link>
          </div>

          <div className="pt-8 border-t border-white/5 text-[0.7rem] font-mono text-neutral-500 flex flex-wrap items-center gap-x-6 gap-y-2" data-testid="splash-meta">
            <a href="mailto:wayseer@interdependentway.org" className="hover:text-accent-cyan" data-testid="splash-email-link">
              wayseer@interdependentway.org
            </a>
            <span>·</span>
            <span>per-user daily demo budget on the emergent key</span>
            <span>·</span>
            <span>byok keys never leave your account</span>
          </div>
        </div>

        <aside className="space-y-4 lg:pt-12" data-testid="splash-features">
          <Feature icon={<Lightning size={18} />} title="Six lattice modes"
                   body="From a raw model to bare a0(<model>) to native a0(zfae) — pick how much canon you want in the loop, per turn." />
          <Feature icon={<ShieldCheck size={18} />} title="Thirteen sentinels"
                   body="Provenance, drift, safety, reversibility — each one is editable, halts on its own threshold, and waits for your override." />
          <Feature icon={<GoogleLogo size={18} />} title="Sign in your way"
                   body="Username + 16-char passphrase, Google, or GitHub — same account, same agents, same canon." />
          <Feature icon={<GithubLogo size={18} />} title="Open-loop spec"
                   body="Every module declares its own contract. The living spec tab parses it directly from the code." />
        </aside>
      </section>
    </div>
  );
}

function Feature({ icon, title, body }) {
  return (
    <div className="border border-white/10 bg-bg-panel p-4 space-y-1.5" data-testid={`splash-feature-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex items-center gap-2 text-accent-cyan/90">
        {icon}
        <span className="font-mono text-xs uppercase tracking-wider">{title}</span>
      </div>
      <p className="text-[0.75rem] font-mono leading-relaxed text-neutral-400">{body}</p>
    </div>
  );
}
