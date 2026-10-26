import React from 'react';
import { ArrowLeftRight, ChevronLeft, ChevronRight, Lock, LockOpen, Sparkles } from 'lucide-react';
import { ResponseMarkdown } from './ResponseMarkdown';

function responseIdOf(item, promptId) {
  return item.message_id || `${promptId}-${item.instance_id || item.model}`;
}

export function ChatResponseComparator({ promptId, responses, synthesisBasket, onToggleSynthesisBlock }) {
  const responseIds = responses.map((item) => responseIdOf(item, promptId));
  const [leftId, setLeftId] = React.useState(responseIds[0] || '');
  const [rightId, setRightId] = React.useState(responseIds[1] || responseIds[0] || '');
  const [lockLeft, setLockLeft] = React.useState(false);
  const [lockRight, setLockRight] = React.useState(false);
  const [carouselIndex, setCarouselIndex] = React.useState(0);

  React.useEffect(() => {
    const first = responseIds[0] || '';
    const second = responseIds[1] || first;
    setLeftId(first);
    setRightId(second);
    setLockLeft(false);
    setLockRight(false);
    setCarouselIndex(0);
  }, [promptId, responses.length]);

  const byId = React.useMemo(() => {
    const map = {};
    responses.forEach((item) => { map[responseIdOf(item, promptId)] = item; });
    return map;
  }, [responses, promptId]);

  const left = byId[leftId];
  const right = byId[rightId];
  const remaining = responses.filter((item) => {
    const id = responseIdOf(item, promptId);
    return id !== leftId && id !== rightId;
  });
  const carouselItem = remaining.length > 0 ? remaining[((carouselIndex % remaining.length) + remaining.length) % remaining.length] : null;

  const toSynthesisBlock = (item) => ({
    source_type: 'chat_prompt_response',
    source_id: responseIdOf(item, promptId),
    source_label: `Prompt ${promptId} · ${item.instance_name}`,
    instance_id: item.instance_id,
    instance_name: item.instance_name,
    model: item.model,
    content: item.content,
  });

  const placeInOpenSlot = (item) => {
    const nextId = responseIdOf(item, promptId);
    if (!lockLeft && nextId !== rightId) {
      setLeftId(nextId);
      return;
    }
    if (!lockRight && nextId !== leftId) {
      setRightId(nextId);
    }
  };

  const swapSlots = () => {
    if (lockLeft || lockRight) return;
    setLeftId(rightId);
    setRightId(leftId);
  };

  const Slot = ({ side, item, itemId, locked, onToggleLock }) => {
    if (!item) {
      return <div className="rounded-2xl border border-dashed border-zinc-700 p-4 text-xs text-zinc-500">No response in this slot.</div>;
    }
    const queued = synthesisBasket.some((block) => block.source_id === itemId);
    return (
      <article className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4" data-testid={`chat-compare-slot-${side}`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">{side} slot</div>
            <div className="mt-1 text-sm font-medium text-zinc-100">{item.instance_name}</div>
            <div className="text-[11px] text-zinc-500">{item.model}</div>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={onToggleLock} className={`rounded-xl border px-2 py-1 text-xs ${locked ? 'border-amber-500/30 bg-amber-500/10 text-amber-200' : 'border-zinc-800 text-zinc-300'}`} data-testid={`chat-compare-lock-${side}-button`}>
              <span className="flex items-center gap-1">{locked ? <Lock size={12} /> : <LockOpen size={12} />} {locked ? 'Locked model' : 'Lock model'}</span>
            </button>
            <button
              type="button"
              onClick={() => onToggleSynthesisBlock(toSynthesisBlock(item))}
              className={`rounded-xl border px-2 py-1 text-xs ${queued ? 'border-violet-500/30 bg-violet-500/10 text-violet-300' : 'border-zinc-800 text-zinc-300 hover:text-white'}`}
              data-testid={`chat-compare-queue-${side}-button`}
            >
              <span className="flex items-center gap-1"><Sparkles size={11} /> {queued ? 'Queued' : 'Queue'}</span>
            </button>
          </div>
        </div>
        <div className="mt-3 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
          <ResponseMarkdown content={item.content} fontScale={1} />
        </div>
      </article>
    );
  };

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="chat-openai-style-compare">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">OpenAI-style compare view</h3>
          <p className="text-xs text-zinc-500">Two visible responses per prompt. Lock model identity on either slot, then rotate others via carousel.</p>
        </div>
        <button type="button" onClick={swapSlots} disabled={lockLeft || lockRight} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40" data-testid="chat-compare-swap-button">
          <span className="flex items-center gap-2"><ArrowLeftRight size={13} /> Swap slots</span>
        </button>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <Slot side="left" item={left} itemId={leftId} locked={lockLeft} onToggleLock={() => setLockLeft((prev) => !prev)} />
        <Slot side="right" item={right} itemId={rightId} locked={lockRight} onToggleLock={() => setLockRight((prev) => !prev)} />
      </div>

      <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3" data-testid="chat-compare-carousel">
        <div className="mb-2 text-xs text-zinc-400">Additional responses ({remaining.length})</div>
        {carouselItem ? (
          <div className="space-y-3">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3" data-testid="chat-compare-carousel-item">
              <div className="text-sm text-zinc-100">{carouselItem.instance_name}</div>
              <div className="text-[11px] text-zinc-500">{carouselItem.model}</div>
              <div className="mt-2 line-clamp-4 text-xs text-zinc-300">{carouselItem.content}</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button type="button" onClick={() => setCarouselIndex((prev) => prev - 1)} className="rounded-xl border border-zinc-800 px-2 py-1 text-xs text-zinc-300" data-testid="chat-compare-carousel-prev-button"><span className="flex items-center gap-1"><ChevronLeft size={12} /> Prev</span></button>
              <button type="button" onClick={() => setCarouselIndex((prev) => prev + 1)} className="rounded-xl border border-zinc-800 px-2 py-1 text-xs text-zinc-300" data-testid="chat-compare-carousel-next-button"><span className="flex items-center gap-1">Next <ChevronRight size={12} /></span></button>
              <button type="button" onClick={() => placeInOpenSlot(carouselItem)} className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200" data-testid="chat-compare-carousel-place-button">Compare in open slot</button>
            </div>
          </div>
        ) : (
          <div className="text-xs text-zinc-500">No overflow responses for this prompt yet.</div>
        )}
      </div>
    </section>
  );
}
