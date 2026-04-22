"use client";
import { useEffect, useState } from "react";
import { getCheckpoint, getStatus, pauseAgent, resumeAgent, setGoal } from "@/lib/api";
import type { AgentStatus, Checkpoint } from "@/lib/types";

export default function SettingsPage() {
  const [ck, setCk] = useState<Checkpoint | null>(null);
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [goal, setGoalText] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const load = async () => {
    setStatus(await getStatus());
    try { setCk(await getCheckpoint()); } catch { setCk(null); }
  };
  useEffect(() => { load(); }, []);

  const submitGoal = async () => {
    setMsg(null);
    try {
      const r = await setGoal(goal);
      setMsg({ kind: "ok", text: `Goal set: ${r.goal}` });
      load();
    } catch (e: any) {
      setMsg({ kind: "err", text: e.message || String(e) });
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <section className="rounded-lg border border-border bg-card p-4">
        <div className="text-sm font-semibold mb-2">Configuration</div>
        <Row k="LLM provider" v={ck?.llm_provider || "—"} />
        <Row k="Model" v={ck?.model || "—"} />
        <Row k="API URL" v={ck?.api_url || "—"} />
        <Row k="Checkpoint interval" v={`${ck?.checkpoint_interval ?? "—"}s`} />
        <Row k="Replan interval" v={`${ck?.replan_interval ?? "—"}s`} />
      </section>

      <section className="rounded-lg border border-border bg-card p-4 space-y-3">
        <div className="text-sm font-semibold">Inject New Goal</div>
        {status?.status === "running" && (
          <div className="rounded border border-yellow-600/50 bg-yellow-600/10 text-yellow-300 text-sm p-2">
            Agent is currently running. Setting a new goal requires the agent to be paused or stopped first.
          </div>
        )}
        <textarea
          className="w-full bg-background border border-border rounded p-2 min-h-[120px]"
          placeholder="Describe the new top-level goal…"
          value={goal}
          onChange={(e) => setGoalText(e.target.value)}
        />
        <div className="flex justify-end">
          <button className="px-3 py-1.5 text-sm rounded bg-primary text-primary-foreground" onClick={submitGoal}>Set Goal</button>
        </div>
        {msg && (
          <div className={`text-sm ${msg.kind === "ok" ? "text-green-400" : "text-red-400"}`}>{msg.text}</div>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-4 space-y-3">
        <div className="text-sm font-semibold">Pause / Resume</div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 text-sm rounded bg-yellow-600/40" onClick={async () => { await pauseAgent(); load(); }}>Pause</button>
          <button className="px-3 py-1.5 text-sm rounded bg-green-600/40" onClick={async () => { await resumeAgent(); load(); }}>Resume</button>
        </div>
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: any }) {
  return (
    <div className="flex justify-between py-1 text-sm border-b border-border/50 last:border-0">
      <span className="text-muted-foreground">{k}</span>
      <span className="font-mono">{String(v)}</span>
    </div>
  );
}
