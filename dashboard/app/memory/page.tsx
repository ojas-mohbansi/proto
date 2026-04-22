"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { getEpisodes, getMemoryStats, pruneMemory, searchMemory } from "@/lib/api";
import type { Episode, MemoryStats } from "@/lib/types";
import MemoryTable from "@/components/MemoryTable";

const PAGE = 50;

export default function MemoryPage() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [page, setPage] = useState(0);
  const [q, setQ] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [showPrune, setShowPrune] = useState(false);
  const [days, setDays] = useState(90);
  const [pruneMsg, setPruneMsg] = useState("");

  const refresh = async () => {
    setStats(await getMemoryStats());
    if (q.trim()) setEpisodes(await searchMemory(q));
    else setEpisodes(await getEpisodes(PAGE, page * PAGE));
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, [page]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      if (q.trim()) setEpisodes(await searchMemory(q));
      else setEpisodes(await getEpisodes(PAGE, page * PAGE));
    }, 400);
  }, [q]); // eslint-disable-line

  const headerStats = useMemo(() => stats && (
    <div className="flex flex-wrap gap-3 text-sm">
      <Stat label="total" v={stats.total_episodes} />
      <Stat label="success" v={stats.successful_episodes} cls="text-green-400" />
      <Stat label="failed" v={stats.failed_episodes} cls="text-red-400" />
      <Stat label="tasks" v={stats.unique_tasks} />
      <Stat label="oldest" v={stats.oldest_episode || "—"} />
    </div>
  ), [stats]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Memory</h1>
        <button className="px-3 py-1.5 text-sm rounded bg-destructive/30 hover:bg-destructive/50" onClick={() => setShowPrune(true)}>
          Prune Old Memories
        </button>
      </div>

      {headerStats}

      <input
        placeholder="Search memory…"
        className="w-full bg-card border border-border rounded px-3 py-2"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      <MemoryTable episodes={episodes} />

      {!q && (
        <div className="flex items-center gap-3 text-sm">
          <button disabled={page === 0} className="px-3 py-1 rounded bg-secondary disabled:opacity-40" onClick={() => setPage(p => Math.max(0, p - 1))}>Previous</button>
          <span className="text-muted-foreground">page {page + 1}</span>
          <button className="px-3 py-1 rounded bg-secondary" onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      )}

      {showPrune && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" onClick={() => setShowPrune(false)}>
          <div className="w-full max-w-sm rounded-lg bg-card border border-border p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="text-lg font-semibold">Prune Old Memories</div>
            <label className="text-xs text-muted-foreground">Older than (days)</label>
            <input type="number" className="w-full bg-background border border-border rounded px-2 py-1.5" value={days} onChange={(e) => setDays(parseInt(e.target.value || "0"))} />
            {pruneMsg && <div className="text-sm text-green-400">{pruneMsg}</div>}
            <div className="flex justify-end gap-2 pt-1">
              <button className="px-3 py-1.5 text-sm rounded bg-secondary" onClick={() => setShowPrune(false)}>Cancel</button>
              <button className="px-3 py-1.5 text-sm rounded bg-destructive text-destructive-foreground" onClick={async () => {
                const r = await pruneMemory(days);
                setPruneMsg(`Deleted ${r.deleted} rows`);
                refresh();
              }}>Prune</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, v, cls = "" }: { label: string; v: any; cls?: string }) {
  return (
    <div className="px-3 py-1 rounded bg-card border border-border">
      <span className="text-muted-foreground mr-2">{label}</span>
      <span className={`font-mono ${cls}`}>{String(v)}</span>
    </div>
  );
}
