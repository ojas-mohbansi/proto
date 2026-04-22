import type {
  AgentStatus, Checkpoint, Episode, LogFile, MemoryStats, Task, TaskStats,
} from "./types";

export const API_PATH = process.env.NEXT_PUBLIC_API_PATH || "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_PATH}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!r.ok) {
    let msg = r.statusText;
    try { const j = await r.json(); msg = j.detail || j.message || msg; } catch {}
    throw new Error(`${r.status} ${msg}`);
  }
  if (r.status === 204) return undefined as unknown as T;
  return r.json();
}

export const getStatus = () => req<AgentStatus>("/agent/status");
export const getCheckpoint = () => req<Checkpoint>("/agent/checkpoint");
export const setGoal = (goal: string) =>
  req<{ ok: boolean; goal: string }>("/agent/goal", { method: "POST", body: JSON.stringify({ goal }) });
export const pauseAgent = () => req("/agent/pause", { method: "POST" });
export const resumeAgent = () => req("/agent/resume", { method: "POST" });

export const getAllTasks = () => req<Task[]>("/tasks/");
export const getTaskStats = () => req<TaskStats>("/tasks/stats");
export const getTaskTree = () => req<{ tree: string }>("/tasks/tree");
export const getTaskById = (id: string) => req<Task>(`/tasks/${id}`);
export const addTask = (body: { goal: string; parent_id?: string | null; completion_condition?: string }) =>
  req<Task>("/tasks/", { method: "POST", body: JSON.stringify(body) });
export const updateTaskGoal = (id: string, goal: string) =>
  req(`/tasks/${id}/goal`, { method: "PUT", body: JSON.stringify({ goal }) });
export const updateTaskStatus = (id: string, status: string, reason = "") =>
  req(`/tasks/${id}/status`, { method: "PUT", body: JSON.stringify({ status, reason }) });
export const deleteTask = (id: string) => req(`/tasks/${id}`, { method: "DELETE" });

export const getMemoryStats = () => req<MemoryStats>("/memory/stats");
export const getEpisodes = (limit = 100, offset = 0, taskId?: string) => {
  const p = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (taskId) p.set("task_id", taskId);
  return req<Episode[]>(`/memory/episodes?${p}`);
};
export const searchMemory = (q: string) => req<Episode[]>(`/memory/search?q=${encodeURIComponent(q)}`);
export const pruneMemory = (days?: number) => {
  const p = days ? `?days=${days}` : "";
  return req<{ ok: boolean; deleted: number }>(`/memory/prune${p}`, { method: "DELETE" });
};

export const getLogFiles = () => req<LogFile[]>("/logs/files");
export const getLogTail = (filename = "most recent", lines = 200) =>
  req<{ file: string; lines: string[] }>(`/logs/tail?filename=${encodeURIComponent(filename)}&lines=${lines}`);
