"use client";
import { useEffect, useState } from "react";
import { addTask, getAllTasks, getTaskStats } from "@/lib/api";
import type { Task, TaskStats } from "@/lib/types";
import TaskTable from "@/components/TaskTable";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [open, setOpen] = useState(false);
  const [goal, setGoal] = useState("");
  const [parentId, setParentId] = useState("");
  const [completion, setCompletion] = useState("");

  const refresh = async () => {
    setTasks(await getAllTasks());
    setStats(await getTaskStats());
  };
  useEffect(() => { refresh(); }, []);

  const submit = async () => {
    if (!goal.trim()) return;
    await addTask({ goal, parent_id: parentId || null, completion_condition: completion });
    setGoal(""); setParentId(""); setCompletion(""); setOpen(false); refresh();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tasks</h1>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 text-sm rounded bg-secondary hover:bg-accent" onClick={refresh}>Refresh</button>
          <button className="px-3 py-1.5 text-sm rounded bg-primary text-primary-foreground" onClick={() => setOpen(true)}>Add Task</button>
        </div>
      </div>

      {stats && (
        <div className="flex gap-3 text-sm">
          {(["total","pending","active","done","failed","blocked"] as const).map(k => (
            <div key={k} className="px-3 py-1 rounded bg-card border border-border">
              <span className="text-muted-foreground mr-2">{k}</span>
              <span className="font-mono">{stats[k]}</span>
            </div>
          ))}
        </div>
      )}

      <TaskTable tasks={tasks} onRefresh={refresh} />

      {open && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" onClick={() => setOpen(false)}>
          <div className="w-full max-w-md rounded-lg bg-card border border-border p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="text-lg font-semibold">Add Task</div>
            <div>
              <label className="text-xs text-muted-foreground">Goal</label>
              <input className="w-full mt-1 bg-background border border-border rounded px-2 py-1.5" value={goal} onChange={(e) => setGoal(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Parent ID (optional)</label>
              <input className="w-full mt-1 bg-background border border-border rounded px-2 py-1.5 font-mono" value={parentId} onChange={(e) => setParentId(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Completion condition (optional)</label>
              <input className="w-full mt-1 bg-background border border-border rounded px-2 py-1.5" value={completion} onChange={(e) => setCompletion(e.target.value)} />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button className="px-3 py-1.5 text-sm rounded bg-secondary" onClick={() => setOpen(false)}>Cancel</button>
              <button className="px-3 py-1.5 text-sm rounded bg-primary text-primary-foreground" onClick={submit}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
