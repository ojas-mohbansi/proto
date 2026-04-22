// Usage: !stats
const { sendReply, callApi } = require("../utils/helpers");

module.exports = {
  name: "stats",
  description: "Show combined agent statistics",
  async execute(sock, msg, args, db, config) {
    const [s, t, m] = await Promise.all([
      callApi("/agent/status", "GET", null, config),
      callApi("/tasks/stats", "GET", null, config),
      callApi("/memory/stats", "GET", null, config),
    ]);
    const out = [
      `*Agent*: ${s.status}${s.paused ? " (paused)" : ""}`,
      `LLM: ${s.llm_provider} (${s.llm_model}) — ${s.ollama_available ? "online" : "offline"}`,
      "",
      "*Tasks*",
      `total ${t.total} | pending ${t.pending} | active ${t.active} | done ${t.done} | failed ${t.failed} | blocked ${t.blocked}`,
      "",
      "*Memory*",
      `total ${m.total_episodes} | ok ${m.successful_episodes} | failed ${m.failed_episodes} | tasks ${m.unique_tasks}`,
      `oldest ${m.oldest_episode || "—"}`,
    ].join("\n");
    await sendReply(sock, msg, out);
  },
};
