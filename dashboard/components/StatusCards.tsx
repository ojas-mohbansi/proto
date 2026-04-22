"use client";
import type { AgentStatus } from "@/lib/types";

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-xs uppercase text-muted-foreground tracking-wider">{title}</div>
      <div className="mt-2 text-lg">{children}</div>
    </div>
  );
}

export default function StatusCards({ data }: { data?: AgentStatus }) {
  const running = data?.status === "running";
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <Card title="Agent Status">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2.5 h-2.5 rounded-full ${
              running ? "bg-green-500 animate-pulse" : "bg-red-500"
            }`}
          />
          <span>{running ? "Running" : "Stopped"}</span>
        </div>
      </Card>
      <Card title="Current Goal">
        <span className="text-sm">{(data?.goal || "—").slice(0, 80)}</span>
      </Card>
      <Card title="Tasks Done">
        <span className="text-green-400">{data?.tasks_completed ?? 0}</span>
      </Card>
      <Card title="Tasks Failed">
        <span className="text-red-400">{data?.tasks_failed ?? 0}</span>
      </Card>
      <Card title="Mode">
        {data?.paused ? (
          <span className="px-2 py-0.5 rounded bg-yellow-600/30 text-yellow-300 text-sm">Paused</span>
        ) : (
          <span className="px-2 py-0.5 rounded bg-green-600/30 text-green-300 text-sm">Active</span>
        )}
      </Card>
    </div>
  );
}
