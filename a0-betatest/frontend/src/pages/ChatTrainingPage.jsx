// === MODULE_BUILD ===
// id: fe_page_chat_training
//   module_name: ChatTrainingPage
//   module_kind: ui_page
//   summary: standalone Chat Training tab — inspect the substrate a training turn touches. A single-turn readout (POST /api/training/readout) renders the turn's UCNS-native embedding as a unit-circle phase disk (one dot per lane, placed by angle, colored by Mobius face) with its phase coherence, the six-family EDCM projection (CM/DA/DRIFT/DVG/INT/TBF) with 0.80/0.20 alert bands, and the three-core gonal disk (phi content-phase / omega bone-density / psi coherence). A session builder (POST /api/training/disk-stack) folds a batch of utterances into a cylindrical disk stack of chapter-scale gonols — one 157-gonal disk per depth-rung (leaf..chapter), the chapter rung being the phase-product (⊠) recomposition. Read-only inspection; weight training stays on the Training Room. Surfaces the recompose-only + UCNS-G/non-absolute firewalls on every result.
//   owner: Erin Spencer
//   public_surface: ChatTrainingPage
//   internal_surface: PhaseDisk, EdcmBars, GonalCores, DiskRow
//   auth_boundary: cookie
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; remove /chat-training route + nav item
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_chat_training_boundaries
//   summary: reads embedding/EDCM/gonal readouts + disk stacks; no writes, no storage
//   auth_boundary: cookie
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_chat_training
//   summary: UCNS-native embedding + EDCM + cylindrical gonal disk-stack inspector
//   exposes: ChatTrainingPage
//   boundaries: auth:cookie, storage:none, network:external, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useState } from "react";
import { CirclesThree, Play, Stack, Waveform } from "@phosphor-icons/react";
import { api } from "../lib/api";
import { Panel, Pill, Stat, AsciiLoader } from "../components/Panel";

const TWO16 = 65536;
const EDCM_LABELS = { cm: "CM constraint", da: "DA dissonance", drift: "DRIFT topic",
  dvg: "DVG divergence", int: "INT intensity", tbf: "TBF balance" };
const BAND_TONE = { high: "rose", low: "cyan", nominal: "emerald" };
// Static (JIT-safe) class strings — Tailwind can't see interpolated names.
const BAND_BAR = { high: "bg-accent-rose/60", low: "bg-accent-cyan/60", nominal: "bg-accent-emerald/60" };
const CORE_TEXT = { cyan: "text-accent-cyan", amber: "text-accent-amber", emerald: "text-accent-emerald" };

// One dot per lane on the unit circle, placed by its 16-bit angle, colored by
// its Mobius face (+1 cyan / -1 violet). This IS the UCNS-native embedding —
// phase streams over the carrier, not a dense vector.
function PhaseDisk({ angleBits = [], chirality = [], size = 168 }) {
  const R = size / 2;
  const r = R - 14;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} data-testid="ct-phase-disk">
      <circle cx={R} cy={R} r={r} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
      <line x1={R} y1={R - r} x2={R} y2={R + r} stroke="rgba(255,255,255,0.06)" />
      <line x1={R - r} y1={R} x2={R + r} y2={R} stroke="rgba(255,255,255,0.06)" />
      {angleBits.map((a, i) => {
        const th = (2 * Math.PI * a) / TWO16;
        const cx = R + r * Math.cos(th - Math.PI / 2);
        const cy = R + r * Math.sin(th - Math.PI / 2);
        const plus = (chirality[i] ?? 1) > 0;
        return <circle key={i} cx={cx} cy={cy} r={2.4}
          fill={plus ? "rgba(34,211,238,0.85)" : "rgba(167,139,250,0.85)"} />;
      })}
    </svg>
  );
}

function EdcmBars({ metrics = {}, alerts = {} }) {
  return (
    <div className="space-y-1.5" data-testid="ct-edcm-bars">
      {Object.keys(EDCM_LABELS).map(k => {
        const v = metrics[k] ?? 0;
        const band = alerts[k] || "nominal";
        const tone = BAND_TONE[band];
        return (
          <div key={k} className="flex items-center gap-2" data-testid={`ct-edcm-${k}`}>
            <span className="w-28 font-mono text-[0.6rem] text-neutral-400">{EDCM_LABELS[k]}</span>
            <div className="flex-1 h-2.5 bg-bg-surface border border-white/10 relative">
              <div className={`h-full ${BAND_BAR[band]}`} style={{ width: `${Math.round(v * 100)}%` }} />
            </div>
            <span className="w-10 text-right font-mono text-[0.6rem] text-neutral-300">{v.toFixed(2)}</span>
            <Pill tone={tone}>{band}</Pill>
          </div>
        );
      })}
    </div>
  );
}

function GonalCores({ phi, omega, psi }) {
  const cores = [
    { k: "φ phi", sub: "content-phase", v: phi, tone: "cyan" },
    { k: "ω omega", sub: "bone-density", v: omega, tone: "amber" },
    { k: "ψ psi", sub: "coherence", v: psi, tone: "emerald" },
  ];
  return (
    <div className="grid grid-cols-3 gap-3" data-testid="ct-gonal-cores">
      {cores.map(c => (
        <div key={c.k} className="border border-white/10 p-3 text-center" data-testid={`ct-core-${c.k[0]}`}>
          <div className={`font-mono text-lg ${CORE_TEXT[c.tone]}`}>{(c.v ?? 0).toFixed(3)}</div>
          <div className="font-mono text-[0.65rem] text-neutral-300">{c.k}</div>
          <div className="font-mono text-[0.55rem] text-neutral-600">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}

function DiskRow({ disk, chapter }) {
  const total = disk.face_plus + disk.face_minus || 1;
  return (
    <tr className={`border-b border-white/5 ${chapter ? "bg-violet-400/5" : "hover:bg-bg-surface"}`}
      data-testid={`ct-disk-${disk.grain}`}>
      <td className="p-2 font-mono text-xs text-white">
        {chapter ? <span className="text-violet-300">{disk.grain} ⊠</span> : disk.grain}
      </td>
      <td className="p-2 font-mono text-[0.65rem] text-neutral-500">{disk.depth}</td>
      <td className="p-2 font-mono text-[0.65rem] text-accent-cyan">{disk.phi.toFixed(3)}</td>
      <td className="p-2 font-mono text-[0.65rem] text-accent-amber">{disk.omega.toFixed(3)}</td>
      <td className="p-2 font-mono text-[0.65rem] text-accent-emerald">{disk.psi.toFixed(3)}</td>
      <td className="p-2">
        <div className="h-2 w-24 flex border border-white/10" title={`+${disk.face_plus} / -${disk.face_minus}`}>
          <div className="h-full bg-accent-cyan/50" style={{ width: `${(disk.face_plus / total) * 100}%` }} />
          <div className="h-full bg-violet-400/50" style={{ width: `${(disk.face_minus / total) * 100}%` }} />
        </div>
      </td>
      <td className="p-2 font-mono text-[0.55rem] text-neutral-600">{disk.embedding_hash.slice(0, 10)}</td>
    </tr>
  );
}

export default function ChatTrainingPage() {
  const [text, setText] = useState("The system must not delete the constraint; preserve every operator.");
  const [prev, setPrev] = useState("keep the loop closed and every operator intact");
  const [readout, setReadout] = useState(null);
  const [rLoading, setRLoading] = useState(false);
  const [rErr, setRErr] = useState(null);

  const [turns, setTurns] = useState(
    "keep the loop closed\nwe must not open it\nhold the frontier line\nrecompose, never decompose");
  const [stack, setStack] = useState(null);
  const [sLoading, setSLoading] = useState(false);
  const [sErr, setSErr] = useState(null);

  const turnList = turns.split("\n").map(t => t.trim()).filter(Boolean);

  async function runReadout() {
    if (!text.trim()) return;
    setRLoading(true); setRErr(null); setReadout(null);
    try {
      setReadout(await api.trainingReadout({ text, prev_text: prev || null }));
    } catch (e) {
      setRErr(e?.response?.data?.detail || e.message || String(e));
    } finally { setRLoading(false); }
  }

  async function runStack() {
    if (turnList.length < 1) return;
    setSLoading(true); setSErr(null); setStack(null);
    try {
      setStack(await api.trainingDiskStack({ turns: turnList, agent_id: "local" }));
    } catch (e) {
      setSErr(e?.response?.data?.detail || e.message || String(e));
    } finally { setSLoading(false); }
  }

  const emb = readout?.embedding;

  return (
    <div className="space-y-5" data-testid="page-chat-training">
      <header className="flex items-center gap-3">
        <CirclesThree size={26} className="text-accent-cyan" />
        <div>
          <h1 className="text-lg font-mono text-white">Chat Training</h1>
          <p className="text-xs font-mono text-neutral-500">
            inspect the UCNS-native embedding, EDCM projection, and cylindrical gonal disk-stack a training turn touches
          </p>
        </div>
      </header>

      <div className="flex flex-wrap gap-2" data-testid="ct-firewalls">
        <Pill tone="emerald">recompose-only</Pill>
        <Pill tone="cyan">public-fixture carrier · 157</Pill>
        <Pill tone="amber">UCNS-G · non-absolute (no theorem transfer)</Pill>
      </div>

      {/* ── single-turn readout ─────────────────────────────────────────── */}
      <Panel title="single turn — embedding · EDCM · gonal" testid="ct-readout-config"
        right={<Waveform size={16} className="text-neutral-500" />}>
        <div className="p-4 space-y-3">
          <label className="block space-y-1">
            <span className="section-overline">turn text</span>
            <textarea data-testid="ct-text" rows={3} value={text} onChange={e => setText(e.target.value)}
              className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
          </label>
          <label className="block space-y-1">
            <span className="section-overline">previous turn (optional — sharpens drift/divergence/balance)</span>
            <textarea data-testid="ct-prev" rows={2} value={prev} onChange={e => setPrev(e.target.value)}
              className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
          </label>
          <button data-testid="ct-readout-btn" disabled={!text.trim() || rLoading} onClick={runReadout}
            className="px-4 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40 flex items-center gap-2">
            <Play size={14} /> {rLoading ? "reading…" : "read turn"}
          </button>
          {rLoading && <AsciiLoader label="embedding + projecting" />}
          {rErr && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="ct-readout-err">{String(rErr)}</div>}
        </div>
      </Panel>

      {readout && (
        <div className="grid md:grid-cols-2 gap-4" data-testid="ct-readout">
          <Panel title="UCNS-native embedding — unit-circle phase disk" testid="ct-embed-panel">
            <div className="p-4 flex flex-col items-center gap-3">
              <PhaseDisk angleBits={emb?.angle_bits} chirality={emb?.chirality} />
              <div className="grid grid-cols-3 gap-3 w-full">
                <Stat label="coherence ψ" value={Number(readout.coherence).toFixed(3)} tone="emerald" />
                <Stat label="carrier" value={emb?.carrier} tone="cyan" />
                <Stat label="lanes" value={emb?.lanes} tone="cyan" />
              </div>
              <div className="w-full font-mono text-[0.55rem] text-neutral-600 break-all">hash {emb?.canonical_hash}</div>
            </div>
          </Panel>

          <div className="space-y-4">
            <Panel title="EDCM projection — six families" testid="ct-edcm-panel">
              <div className="p-4"><EdcmBars metrics={readout.edcm?.metrics} alerts={readout.edcm?.alerts} /></div>
            </Panel>
            <Panel title="three-core gonal" testid="ct-gonal-panel">
              <div className="p-4 space-y-3">
                <GonalCores phi={readout.disk?.phi} omega={readout.disk?.omega} psi={readout.disk?.psi} />
                <div className="font-mono text-[0.55rem] text-neutral-600">
                  raised operator fields: {readout.edcm?.raised_field_count}
                </div>
              </div>
            </Panel>
          </div>
        </div>
      )}

      {/* ── cylindrical disk stack ──────────────────────────────────────── */}
      <Panel title="session — cylindrical disk stack of chapter-scale gonols" testid="ct-stack-config"
        right={<Stack size={16} className="text-neutral-500" />}>
        <div className="p-4 space-y-3">
          <label className="block space-y-1">
            <span className="section-overline">session utterances (one per line)</span>
            <textarea data-testid="ct-turns" rows={5} value={turns} onChange={e => setTurns(e.target.value)}
              className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
            <span className="text-[0.6rem] font-mono text-neutral-600">
              {turnList.length} utterance(s) → 5 disks (leaf · circle · seed · core · chapter); chapter = ⊠ phase-product recompose
            </span>
          </label>
          <button data-testid="ct-stack-btn" disabled={turnList.length < 1 || sLoading} onClick={runStack}
            className="px-4 py-2 border border-violet-400/40 text-violet-300 font-mono text-xs uppercase tracking-wider hover:bg-violet-400/10 disabled:opacity-40 flex items-center gap-2">
            <Play size={14} /> {sLoading ? "building…" : "build disk stack"}
          </button>
          {sLoading && <AsciiLoader label="folding session into chapter gonol" />}
          {sErr && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="ct-stack-err">{String(sErr)}</div>}
        </div>
      </Panel>

      {stack && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="ct-stack-metrics">
            <Stat label="chapter ψ" value={Number(stack.chapter_psi).toFixed(4)} tone="emerald" />
            <Stat label="utterances" value={stack.session_turns} tone="cyan" />
            <Stat label="carrier" value={stack.carrier_arity} tone="cyan" />
            <Stat label="geometry" value={stack.public_fixture_carrier ? "fixture" : "degraded"} tone="amber" />
          </div>
          <Panel title={`disk stack · ${stack.disks.length} rungs · ${stack.geometry_status}`} testid="ct-stack">
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono" data-testid="ct-stack-table">
                <thead>
                  <tr className="border-b border-white/10 text-neutral-500">
                    <th className="text-left p-2">rung</th>
                    <th className="text-left p-2">z</th>
                    <th className="text-left p-2">φ</th>
                    <th className="text-left p-2">ω</th>
                    <th className="text-left p-2">ψ</th>
                    <th className="text-left p-2">faces ±</th>
                    <th className="text-left p-2">hash</th>
                  </tr>
                </thead>
                <tbody>
                  {stack.disks.map(d => (
                    <DiskRow key={d.grain} disk={d} chapter={d.grain === "chapter"} />
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
