// Usage: !tasks [limit]
const { sendReply, callApi, formatTask } = require("../utils/helpers");

module.exports = {
  name: "tasks",
  description: "List tasks",
  async execute(sock, msg, args, db, config) {
    const limit = Math.max(1, Math.min(50, parseInt(args[0]) || 10));
    const all = await callApi("/tasks/", "GET", null, config);
    if (!all.length) return sendReply(sock, msg, "No tasks found.");
    const shown = all.slice(0, limit);
    const out = [`*Tasks* — ${all.length} total, showing ${shown.length}`].concat(shown.map(formatTask)).join("\n");
    await sendReply(sock, msg, out);
  },
};
