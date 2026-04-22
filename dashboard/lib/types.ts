export interface AgentStatus {
  status: "running" | "stopped";
  last_heartbeat: string | null;
  goal: string | null;
  current_task_id: string | null;
  iteration: number;
  tasks_completed: number;
  tasks_failed: number;
  ollama_available: boolean;
  paused: boolean;
  llm_provider?: string;
  llm_model?: string;
}

export interface Task {
  id: string;
  goal: string;
  parent_id: string | null;
  subtasks: string[];
  status: string;
  created_at: string;
  deadline: string | null;
  completion_condition: string;
  estimated_hours: number;
  attempts: number;
  last_error: string;
  context_summary: string;
}

export interface Episode {
  id: string;
  timestamp: string;
  task_id: string | null;
  action: string;
  result: string;
  success: boolean;
}

export interface MemoryStats {
  total_episodes: number;
  successful_episodes: number;
  failed_episodes: number;
  unique_tasks: number;
  oldest_episode: string | null;
}

export interface TaskStats {
  total: number;
  pending: number;
  active: number;
  done: number;
  failed: number;
  blocked: number;
}

export interface LogFile {
  name: string;
  size: number;
  modified: string;
}

export interface Checkpoint {
  goal?: string;
  iteration?: number;
  tasks_completed?: number;
  tasks_failed?: number;
  current_task_id?: string;
  model?: string;
  api_url?: string;
  checkpoint_interval?: number;
  replan_interval?: number;
  llm_provider?: string;
}
