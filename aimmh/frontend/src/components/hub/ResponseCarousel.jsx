import React from 'react';
import { ChevronDown, ChevronUp, ZoomIn, ZoomOut } from 'lucide-react';
import { ResponsePane } from './ResponsePane';

function averageY(touches) {
  return Array.from(touches).reduce((sum, touch) => sum + touch.clientY, 0) / touches.length;
}

function distance(touches) {
  if (touches.length < 2) return 0;
  const [first, second] = touches;
  return Math.hypot(first.clientX - second.clientX, first.clientY - second.clientY);
}

export function ResponseCarousel({
  items,
  activeIndex,
  setActiveIndex,
  fontScale,
  setFontScale,
  selectedIds,
  feedbackMap,
  onToggleSelected,
  onFeedback,
  onCopy,
  onShare,
  archivedIds = [],
  onToggleArchive = null,
  synthesisIds = [],
  onToggleSynthesis = null,
}) {
  const gestureRef = React.useRef({
    startDistance: 0,
    lastAverageY: 0,
    moved: false,
    gestureType: '',
  });

  const clampIndex = (nextIndex) => Math.max(0, Math.min(items.length - 1, nextIndex));

  const handleTouchStart = (event) => {
    if (event.touches.length >= 2) {
      gestureRef.current = {
        startDistance: distance(event.touches),
        lastAverageY: averageY(event.touches),
        moved: false,
        gestureType: '',
      };
    }
  };

  const resetGesture = () => {
    gestureRef.current = {
      startDistance: 0,
      lastAverageY: 0,
      moved: false,
      gestureType: '',
    };
  };

  const handleTouchMove = (event) => {
    if (event.touches.length < 2) return;
    event.preventDefault();

    const nextDistance = distance(event.touches);
    const nextAverageY = averageY(event.touches);
    const distanceDelta = nextDistance - gestureRef.current.startDistance;
    const deltaY = nextAverageY - gestureRef.current.lastAverageY;

    if (!gestureRef.current.gestureType) {
      if (Math.abs(distanceDelta) > 14 && Math.abs(distanceDelta) > Math.abs(deltaY)) {
        gestureRef.current.gestureType = 'zoom';
      } else if (Math.abs(deltaY) > 55) {
        gestureRef.current.gestureType = 'swipe';
      }
    }

    if (gestureRef.current.gestureType === 'zoom') {
      const zoomDelta = distanceDelta / 150;
      if (Math.abs(zoomDelta) > 0.01) {
        setFontScale((prev) => Math.max(0.85, Math.min(1.9, Number((prev + zoomDelta).toFixed(2)))));
        gestureRef.current.startDistance = nextDistance;
      }
      gestureRef.current.lastAverageY = nextAverageY;
      return;
    }

    if (!gestureRef.current.moved && Math.abs(deltaY) > 80) {
      setActiveIndex((prev) => clampIndex(prev + (deltaY > 0 ? -1 : 1)));
      gestureRef.current.moved = true;
      window.setTimeout(() => {
        gestureRef.current.moved = false;
      }, 220);
    }
    gestureRef.current.lastAverageY = nextAverageY;
  };

  if (items.length === 0) {
    return <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500">No responses available for this stage yet.</div>;
  }

  const current = items[activeIndex] || items[0];

  return (
    <div className="space-y-3" data-testid="response-carousel">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500">
        <div data-testid="response-carousel-hint">Two fingers: swipe vertically to change pane, pinch to zoom. One finger: scroll inside response.</div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setActiveIndex((prev) => clampIndex(prev - 1))} className="rounded-full border border-zinc-800 p-2 text-zinc-300 hover:text-white" data-testid="response-carousel-prev-button"><ChevronUp size={13} /></button>
          <button type="button" onClick={() => setActiveIndex((prev) => clampIndex(prev + 1))} className="rounded-full border border-zinc-800 p-2 text-zinc-300 hover:text-white" data-testid="response-carousel-next-button"><ChevronDown size={13} /></button>
          <button type="button" onClick={() => setFontScale((prev) => Math.max(0.85, Number((prev - 0.05).toFixed(2))))} className="rounded-full border border-zinc-800 p-2 text-zinc-300 hover:text-white" data-testid="response-carousel-zoom-out-button"><ZoomOut size={13} /></button>
          <button type="button" onClick={() => setFontScale((prev) => Math.min(1.9, Number((prev + 0.05).toFixed(2))))} className="rounded-full border border-zinc-800 p-2 text-zinc-300 hover:text-white" data-testid="response-carousel-zoom-in-button"><ZoomIn size={13} /></button>
        </div>
      </div>
      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={resetGesture}
        onTouchCancel={resetGesture}
        className="h-[72vh] touch-none"
        style={{ touchAction: 'none' }}
        data-testid="response-carousel-pane"
      >
        <ResponsePane
          item={current}
          selected={selectedIds.includes(current.run_step_id)}
          fontScale={fontScale}
          feedback={feedbackMap[current.message_id || current.run_step_id]}
          onToggleSelected={() => onToggleSelected(current)}
          onFeedback={(value) => onFeedback(current, value)}
          onCopy={() => onCopy(current)}
          onShare={() => onShare(current)}
          archived={archivedIds.includes(current.run_step_id)}
          onToggleArchive={onToggleArchive ? () => onToggleArchive(current) : null}
          synthesisSelected={synthesisIds.includes(current.run_step_id)}
          onToggleSynthesis={onToggleSynthesis ? () => onToggleSynthesis(current) : null}
        />
      </div>
    </div>
  );
}
