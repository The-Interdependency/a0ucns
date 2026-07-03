// === MODULE_BUILD ===
// id: fe_page_inspector
//   module_name: InspectorPage
//   module_kind: ui_page
//   summary: live inspector for PCNA/PTCA/PCEA skills + msdmd compliance reports (capabilities / module-build / contracts coverage); heartbeat ping
//   owner: Erin Spencer
//   public_surface: InspectorPage
//   internal_surface: none
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_inspector_boundaries
//   summary: read-only inspector
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_inspector
//   summary: inspector dashboard ui
//   exposes: InspectorPage
//   boundaries: auth:none, storage:none, network:external, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Panel, Pill, Stat, AsciiLoader } from "../components/Panel";
import { Heart, ArrowsClockwise } from "@phosphor-icons/react";

const RINGS = ["phi", "psi", "omega", "theta", "sigma", "epsilon"];
const RING_NAMES = {
  phi: "Φ · phi (primary intent)",
  psi: "Ψ · psi (substrate)",
  omega: "Ω · omega (broadcast)",
  theta: "Θ · theta (phase)",
  sigma: "Σ · sigma (sub-encoding)",
  epsilon: "Ε · epsilon (dissonance)",
};


function SkillTile({ scanned, covered, gapsCount, gaps, extra = [], extraSection = null, testid }) {
  const hasGaps = (gapsCount ?? 0) > 0;
  return (
    <div data-testid={testid}>
      <div className="grid grid-cols-3 gap-2 font-mono text-xs">
        <div className="border border-white/10 bg-bg-deep p-3">
          <div className="section-overline">scanned</div>
          <div className="text-2xl text-white">{scanned ?? "—"}</div>
        </div>
        <div className="border border-white/10 bg-bg-deep p-3">
          <div className="section-overline">covered</div>
          <div className="text-2xl text-accent-emerald">{covered ?? "—"}</div>
        </div>
        <div className="border border-white/10 bg-bg-deep p-3">
          <div className="section-overline">gaps</div>
          <div className={"text-2xl " + (hasGaps ? "text-accent-rose" : "text-accent-emerald")}>
            {gapsCount ?? "—"}
          </div>
        </div>
      </div>
      {extra.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {extra.map(([label, value, tone]) => (
            <Pill key={label} tone={tone}>{label}: {value}</Pill>
          ))}
        </div>
      )}
      {hasGaps ? (
        <div className="mt-3 border border-accent-rose/40 bg-rose-500/5 p-3 text-xs font-mono">
          <div className="text-accent-rose mb-2">{gaps.length} file(s) without the block:</div>
          <ul className="space-y-0.5 max-h-[160px] overflow-auto">
            {gaps.slice(0, 30).map(g => <li key={g} className="text-neutral-300">· {g}</li>)}
            {gaps.length > 30 && <li className="text-neutral-500">… {gaps.length - 30} more</li>}
          </ul>
        </div>
      ) : scanned ? (
        <div className="mt-3 text-xs font-mono text-accent-emerald">✓ no gaps · 100% compliance</div>
      ) : null}
      {extraSection}
    </div>
  );
}

export default function InspectorPage() {
  const [snap, setSnap] = useState(null);
  const [intent, setIntent] = useState("");
  const [busy, setBusy] = useState(false);
  const [caps, setCaps] = useState(null);
  const [contracts, setContracts] = useState(null);
  const [modBuild, setModBuild] = useState(null);
  const [skillTab, setSkillTab] = useState("module-build");

  async function load() {
    const [r, cap, con, mb] = await Promise.all([
      api.inspectorSnap(),
      api.skillCapabilities().catch(() => null),
      api.skillContracts().catch(() => null),
      api.skillModuleBuild().catch(() => null),
    ]);
    setSnap(r.agent_card?.snapshot || null);
    setCaps(cap);
    setContracts(con);
    setModBuild(mb);
  }
  useEffect(() => { load(); }, []);

  async function beat() {
    setBusy(true);
    try {
      await api.inspectorBeat(intent || null);
      await load();
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6" data-testid="page-inspector">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl tracking-tighter">PCNA · Inference Engine Inspector</h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl">
            Read-only view of the six-ring engine (Φ Ψ Ω Θ Σ Ε), three 157-seed PTCA cores (phi / psi / omega),
            EDCM scores, Memory-L (N=19) and Memory-S (N=17) caches. Trigger a heartbeat to advance the tick.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost" onClick={load} data-testid="insp-refresh"><ArrowsClockwise size={14}/> refresh</button>
        </div>
      </header>

      <div
        className="relative border border-white/10 bg-bg-panel overflow-hidden"
        style={{
          backgroundImage: "url(https://static.prod-images.emergentagent.com/jobs/c2d14c10-eaf9-49ca-ad1e-339f5025b355/images/7d0ec2e194e2ca69f7eed061da0f99511eec16722c64735fbb67d3520a66f11f.png)",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="absolute inset-0 bg-black/70"></div>
        <div className="relative p-6 grid md:grid-cols-3 gap-4">
          {RINGS.map(k => (
            <div key={k} className="border border-white/15 bg-black/50 p-4">
              <div className="section-overline">{RING_NAMES[k]}</div>
              <div className="font-mono text-3xl text-accent-cyan mt-1" data-testid={`ring-${k}`}>
                {(snap?.ring_signals?.[k] ?? 0).toFixed(4)}
              </div>
              <div className="mt-2 h-1 bg-white/10">
                <div className="h-full bg-accent-cyan" style={{width: `${Math.min(100, ((snap?.ring_signals?.[k] ?? 0) * 100)).toFixed(1)}%`}}></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-4 gap-3">
        <Stat label="tick count"      value={snap?.tick_count ?? 0} tone="cyan"/>
        <Stat label="n primes (cores)" value={snap?.n_primes ?? 157} tone="amber"/>
        <Stat label="memory · lt"     value={(snap?.memory?.lt_capacity ?? 19) + " cap"} tone="emerald"/>
        <Stat label="memory · st"     value={(snap?.memory?.st_capacity ?? 17) + " cap"} tone="emerald"/>
      </div>

      <Panel title="heartbeat" right={busy ? <AsciiLoader label="pulsing"/> : null}>
        <div className="p-4 flex flex-col md:flex-row gap-2 items-stretch md:items-center">
          <input className="input-term flex-1"
                 placeholder="optional intent (drives phi/sigma)…"
                 value={intent}
                 onChange={e => setIntent(e.target.value)}
                 data-testid="insp-intent-input"/>
          <button className="btn-primary" onClick={beat} disabled={busy} data-testid="insp-beat-btn">
            <Heart size={14}/> heartbeat
          </button>
        </div>
      </Panel>

      <Panel title="ptca cores · 3 × 157 primes">
        <div className="p-4 grid md:grid-cols-3 gap-3">
          {snap?.cores && Object.entries(snap.cores).map(([k, c]) => (
            <div key={k} className="border border-white/10 bg-bg-deep p-3" data-testid={`core-${k}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-accent-cyan text-sm">core · {k}</span>
                <Pill tone="cyan">{c.tensor.n_primes} primes</Pill>
              </div>
              <div className="font-mono text-[0.7rem] space-y-1 text-neutral-300">
                <div>shape :: [{c.tensor.shape.join(", ")}]</div>
                <div>energy :: <span className="text-accent-amber">{c.tensor.energy}</span></div>
                <div>head :: {c.tensor.primes_head.join(", ")}…</div>
                <div>tail :: …{c.tensor.primes_tail.join(", ")}</div>
                <div>lineage :: {c.lineage_depth}</div>
                <div>head_hash :: <span className="text-neutral-500">{c.lineage_head?.slice(0, 16) || "—"}</span></div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="skill-lib coverage · msdmd / test-build / meta-module-build"
        right={<div className="flex gap-1.5">
          {["module-build", "contracts", "capabilities"].map(t => (
            <button key={t}
              className={"btn-ghost py-1 px-2 text-[0.65rem] " + (skillTab === t ? "active" : "")}
              onClick={() => setSkillTab(t)}
              data-testid={`skill-tab-${t}`}>
              {t}
            </button>
          ))}
        </div>}>
        <div className="p-4 space-y-3" data-testid="skill-panel">
          <div className="text-xs text-neutral-400 font-sans leading-relaxed max-w-3xl">
            Three msdmd-derived skills from <span className="font-mono text-accent-cyan">The-Interdependency/skill-lib</span>.
            Every module declares its <span className="font-mono">MODULE_BUILD</span> manifest and (where applicable) its <span className="font-mono">CONTRACTS</span> block.
            The runners enforce coverage; gap lists stay visible per doctrine.
          </div>

          {skillTab === "module-build" && (
            <SkillTile
              testid="skill-mb"
              scanned={modBuild?.scanned}
              covered={modBuild?.covered}
              gapsCount={modBuild?.gaps_count}
              extra={modBuild ? [
                ["valid", modBuild.valid_count, "emerald"],
                ["invalid", modBuild.invalid_count, modBuild.invalid_count ? "rose" : "emerald"],
              ] : []}
              gaps={modBuild?.gaps || []}
              extraSection={modBuild && (
                <div className="mt-3 grid md:grid-cols-2 gap-3 text-xs font-mono">
                  <div>
                    <div className="section-overline mb-1">by kind</div>
                    {Object.entries(modBuild.by_kind || {}).sort().map(([k, n]) => (
                      <div key={k} className="flex justify-between border-b border-white/5 py-1">
                        <span className="text-neutral-400">{k}</span>
                        <span className="text-accent-cyan">{n}</span>
                      </div>
                    ))}
                  </div>
                  <div>
                    <div className="section-overline mb-1">boundary risk (non-none)</div>
                    {Object.entries(modBuild.boundary_risk || {}).sort((a, b) => b[1] - a[1]).map(([k, n]) => (
                      <div key={k} className="flex justify-between border-b border-white/5 py-1">
                        <span className="text-neutral-400">{k}</span>
                        <span className="text-accent-amber">{n}</span>
                      </div>
                    ))}
                    {!Object.keys(modBuild.boundary_risk || {}).length && <div className="text-neutral-600">no non-none surfaces</div>}
                  </div>
                </div>
              )}
            />
          )}

          {skillTab === "contracts" && (
            <SkillTile
              testid="skill-contracts"
              scanned={(contracts?.results?.length || 0) + (contracts?.untested_count || 0)}
              covered={contracts?.results?.length || 0}
              gapsCount={contracts?.untested_count || 0}
              extra={contracts ? [
                ["pass", contracts.counts?.PASS || 0, "emerald"],
                ["fail", contracts.counts?.FAIL || 0, (contracts.counts?.FAIL || 0) ? "rose" : "emerald"],
                ["error", contracts.counts?.ERROR || 0, (contracts.counts?.ERROR || 0) ? "rose" : "emerald"],
              ] : []}
              gaps={contracts?.untested || []}
              extraSection={contracts && contracts.results?.length > 0 && (
                <div className="mt-3 space-y-1 font-mono text-xs">
                  <div className="section-overline mb-1">contract results</div>
                  {contracts.results.map(r => {
                    const tone = r.status === "PASS" ? "emerald" : r.status === "FAIL" ? "rose" : r.status === "ERROR" ? "rose" : "amber";
                    const sym = { PASS: "✓", FAIL: "✗", ERROR: "!", SKIP: "-" }[r.status] || "?";
                    return (
                      <div key={r.id + (r._file || "")} className="flex items-start gap-2 border-b border-white/5 py-1">
                        <Pill tone={tone}>{sym} {r.status}</Pill>
                        <div className="flex-1 min-w-0">
                          <div className="text-white truncate">{r.id}</div>
                          <div className="text-neutral-500 text-[0.65rem] truncate">{r._file}</div>
                          {r.error && <div className="text-accent-rose text-[0.7rem] mt-1">{r.error}</div>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            />
          )}

          {skillTab === "capabilities" && (
            <SkillTile
              testid="skill-caps"
              scanned={caps?.scanned}
              covered={caps?.covered}
              gapsCount={caps?.gaps_count}
              gaps={caps?.gaps || []}
              extra={[["legacy", "deprecated", "amber"]]}
              extraSection={(
                <div className="mt-2 text-[0.7rem] font-mono text-neutral-500">
                  Legacy CAPABILITIES block coverage. The canonical executors are <span className="text-accent-cyan">module-build</span> and <span className="text-accent-cyan">contracts</span>. Kept as a migration view.
                </div>
              )}
            />
          )}
        </div>
      </Panel>

      <div className="grid md:grid-cols-2 gap-4">
        <Panel title="EDCM · latest scores">
          <div className="p-4 grid grid-cols-2 gap-2 font-mono text-xs">
            {snap?.edcm_latest && Object.entries(snap.edcm_latest).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between border border-white/5 px-3 py-2 bg-bg-deep" data-testid={`edcm-${k}`}>
                <span className="text-neutral-400">{k.toUpperCase()}</span>
                <span className="text-accent-cyan">{Number(v).toFixed(4)}</span>
              </div>
            ))}
            {!snap?.edcm_latest && <div className="text-neutral-500">no edcm scores yet · trigger a heartbeat</div>}
          </div>
        </Panel>

        <Panel title="memory snapshot">
          <div className="p-4 font-mono text-xs space-y-3">
            <div>
              <div className="section-overline">long-term (N={snap?.memory?.lt_capacity})</div>
              <ul className="mt-1 space-y-0.5">
                {(snap?.memory?.lt || []).slice(-8).map((m, i) => <li key={i} className="text-neutral-300">· {m}</li>)}
                {!(snap?.memory?.lt || []).length && <li className="text-neutral-500">— empty —</li>}
              </ul>
            </div>
            <div>
              <div className="section-overline">short-term (N={snap?.memory?.st_capacity})</div>
              <ul className="mt-1 space-y-0.5">
                {(snap?.memory?.st || []).slice(-8).map((m, i) => <li key={i} className="text-neutral-300">· {m}</li>)}
                {!(snap?.memory?.st || []).length && <li className="text-neutral-500">— empty —</li>}
              </ul>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}
