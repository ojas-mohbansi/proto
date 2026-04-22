// Usage: !memory <search query>
const { sendReply, callApi } = require("../utils/helpers");

module.exports = {
  name: "memory",
  description: "Search agent memory",
  async execute(sock, msg, args, db, config) {
    if (!args.length) return sendReply(sock, msg, `Usage: ${config.prefix}memory <query>`);
    const q = args.join(" ");
    const results = await callApi(`/memory/search?q=${encodeURIComponent(q)}`, "GET", null, config);
    if (!results.length) return sendReply(sock, msg, "No matching memories found.");
    const top = results.slice(0, 5).map((e) => {
      const ok = e.success ? "[OK]" : "[X]";
      return `${ok} ${e.timestamp.slice(0, 19)} t=${(e.task_id || "").slice(0,8)}\n  a: ${(e.action || "").slice(0,50)}\n  r: ${(e.result || "").slice(0,50)}`;
    }).join("\n\n");
    await sendReply(sock, msg, `*Memory results* (${results.length})\n\n${top}`);
  },
};
