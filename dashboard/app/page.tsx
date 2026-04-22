"use client";
import useSWR from "swr";
import { getStatus, pauseAgent, resumeAgent } from "@/lib/api";
import StatusCards from "@/components/StatusCards";
import LiveLog from "@/components/LiveLog";

export default function DashboardPage() {
  const { data, error, isLoading, mutate } = useSWR("status", getStatus, { refreshInterval: 3000 });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {error && (
        <div className="rounded border border-destructive/50 bg-destructive/10 text-destructive p-3 text-sm">
          API unreachable: {String(error.message || error)}
        </div>
      )}

      {isLoading && !data ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-border bg-card p-4 h-20 animate-pulse" />
          ))}
        </div>
      ) : (
        <StatusCards data={data} />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="text-xs uppercase text-muted-foreground tracking-wider">Current Task</div>
          <div className="mt-2 text-sm font-mono">{data?.current_task_id || "—"}</div>
          <div className="mt-2 text-sm">{data?.goal || "No goal set."}</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">LLM provider</span>
            <span className={`px-2 py-0.5 rounded text-xs ${data?.ollama_available ? "bg-green-600/30 text-green-300" : "bg-red-600/30 text-red-300"}`}>
              {data?.ollama_available ? "online" : "offline"}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            {data?.llm_provider || "—"} · {data?.llm_model || "—"}
          </div>
          <div className="flex gap-2 pt-2">
            <button
              className="px-3 py-1.5 text-sm rounded bg-yellow-600/40 hover:bg-yellow-600/60"
              onClick={async () => { await pauseAgent(); mutate(); }}
            >Pause Agent</button>
            <button
              className="px-3 py-1.5 text-sm rounded bg-green-600/40 hover:bg-green-600/60"
              onClick={async () => { await resumeAgent(); mutate(); }}
            >Resume Agent</button>
          </div>
        </div>
      </div>

      <div>
        <div className="text-sm text-muted-foreground mb-2">Live log</div>
        <LiveLog />
      </div>
    </div>
  );
}
