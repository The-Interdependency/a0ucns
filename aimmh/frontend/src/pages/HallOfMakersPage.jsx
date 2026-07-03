import React from 'react';
import { ArrowLeft, ExternalLink, HeartHandshake } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { paymentsApi } from '../lib/paymentsApi';

export default function HallOfMakersPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    (async () => {
      try {
        const response = await paymentsApi.getHall();
        setEntries(response.entries || []);
      } catch (error) {
        toast.error(error.message || 'Failed to load Hall of Makers');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 px-4 py-6 text-zinc-100 sm:px-6">
      <div className="mx-auto max-w-4xl space-y-4">
        <button onClick={() => navigate('/chat')} className="inline-flex items-center gap-2 rounded-xl border border-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:border-zinc-700 hover:text-white">
          <ArrowLeft size={14} /> Back to AIMMH
        </button>
        <section className="rounded-3xl border border-zinc-800 bg-zinc-900/60 p-5 sm:p-7">
          <div className="flex items-center gap-2 text-emerald-300"><HeartHandshake size={16} /> Interdependent Makers / Hall of Makers</div>
          <h1 className="mt-2 text-3xl font-semibold text-zinc-50">Those sustaining AIMMH</h1>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-zinc-400">Supporter, Pro, and Team patrons can opt into this page with a name and optional link.</p>
        </section>
        <section className="space-y-3">
          {loading ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 text-sm text-zinc-500">Loading credits…</div>
          ) : entries.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500">No public makers yet.</div>
          ) : entries.map((entry) => (
            <article key={entry.user_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-medium text-zinc-100">{entry.display_name}</h2>
                <span className="rounded-full border border-zinc-800 bg-zinc-950 px-2 py-1 text-[11px] uppercase tracking-[0.2em] text-zinc-400">{entry.tier}</span>
              </div>
              {entry.link && (
                <a href={entry.link} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-sm text-blue-300 hover:text-blue-200">
                  {entry.link} <ExternalLink size={12} />
                </a>
              )}
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}
