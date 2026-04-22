"use client";
import { Fragment, useState } from "react";
import type { Episode } from "@/lib/types";

export default function MemoryTable({ episodes }: { episodes: Episode[] }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <th className="text-left p-2">Timestamp</th>
            <th className="text-left p-2">Task</th>
            <th className="text-left p-2">Action</th>
            <th className="text-left p-2">Result</th>
            <th className="text-left p-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {episodes.map((e) => (
            <Fragment key={e.id}>
              <tr
                className="border-t border-border cursor-pointer hover:bg-accent/30"
                onClick={() => setOpen(open === e.id ? null : e.id)}
              >
                <td className="p-2 font-mono text-xs">{e.timestamp.replace("T", " ").slice(0, 19)}</td>
                <td className="p-2 font-mono text-xs">{(e.task_id || "").slice(0, 8)}</td>
                <td className="p-2">{(e.action || "").slice(0, 60)}</td>
                <td className="p-2">{(e.result || "").slice(0, 60)}</td>
                <td className="p-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${e.success ? "bg-green-600/30 text-green-300" : "bg-red-600/30 text-red-300"}`}>
                    {e.success ? "ok" : "fail"}
                  </span>
                </td>
              </tr>
              {open === e.id && (
                <tr className="bg-background">
                  <td colSpan={5} className="p-3">
                    <div className="text-xs text-muted-foreground mb-1">ACTION</div>
                    <pre className="bg-card p-2 rounded font-mono text-xs whitespace-pre-wrap">{e.action}</pre>
                    <div className="text-xs text-muted-foreground mt-2 mb-1">RESULT</div>
                    <pre className="bg-card p-2 rounded font-mono text-xs whitespace-pre-wrap">{e.result}</pre>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
          {episodes.length === 0 && (
            <tr><td colSpan={5} className="p-6 text-center text-muted-foreground">No memory yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
