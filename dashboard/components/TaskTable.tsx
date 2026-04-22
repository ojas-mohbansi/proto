"use client";
import { useState } from "react";
import type { Task } from "@/lib/types";
import { deleteTask, updateTaskGoal, updateTaskStatus } from "@/lib/api";
import { Check, Edit2, Trash2, X } from "lucide-react";

const STATUS_COLOR: Record<string, string> = {
  DONE: "bg-green-600/30 text-green-300",
  ACTIVE: "bg-blue-600/30 text-blue-300",
  PENDING: "bg-yellow-600/30 text-yellow-300",
  FAILED: "bg-red-600/30 text-red-300",
  BLOCKED: "bg-gray-600/30 text-gray-300",
};

export default function TaskTable({
  tasks,
  onRefresh,
}: { tasks: Task[]; onRefresh: () => void }) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const save = async (id: string) => {
    await updateTaskGoal(id, draft);
    setEditing(null);
    onRefresh();
  };

  const markDone = async (id: string) => { await updateTaskStatus(id, "DONE"); onRefresh(); };
  const markFailed = async (id: string) => {
    const reason = window.prompt("Reason for failure?", "manual mark") || "manual";
    await updateTaskStatus(id, "FAILED", reason); onRefresh();
  };
  const onDelete = async (id: string) => {
    if (!window.confirm("Delete this task and its subtasks?")) return;
    await deleteTask(id); onRefresh();
  };

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <th className="text-left p-2">ID</th>
            <th className="text-left p-2">Goal</th>
            <th className="text-left p-2">Status</th>
            <th className="text-left p-2">Attempts</th>
            <th className="text-left p-2">Est Hours</th>
            <th className="text-left p-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id} className="border-t border-border">
              <td className="p-2 font-mono text-xs">{t.id.slice(0, 8)}</td>
              <td className="p-2">
                {editing === t.id ? (
                  <div className="flex gap-2">
                    <input
                      autoFocus
                      className="flex-1 bg-background border border-border rounded px-2 py-1"
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                    />
                    <button onClick={() => save(t.id)} className="text-green-400"><Check size={16} /></button>
                    <button onClick={() => setEditing(null)} className="text-muted-foreground"><X size={16} /></button>
                  </div>
                ) : (
                  <span>{t.goal}</span>
                )}
              </td>
              <td className="p-2">
                <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLOR[t.status] || "bg-secondary"}`}>
                  {t.status}
                </span>
              </td>
              <td className="p-2">{t.attempts}</td>
              <td className="p-2">{t.estimated_hours}</td>
              <td className="p-2">
                <div className="flex items-center gap-2">
                  <button title="Edit" onClick={() => { setEditing(t.id); setDraft(t.goal); }}>
                    <Edit2 size={14} />
                  </button>
                  <button title="Mark Done" onClick={() => markDone(t.id)} className="text-green-400">
                    <Check size={16} />
                  </button>
                  <button title="Mark Failed" onClick={() => markFailed(t.id)} className="text-red-400">
                    <X size={16} />
                  </button>
                  <button title="Delete" onClick={() => onDelete(t.id)} className="text-muted-foreground">
                    <Trash2 size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
          {tasks.length === 0 && (
            <tr><td colSpan={6} className="p-6 text-center text-muted-foreground">No tasks yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
