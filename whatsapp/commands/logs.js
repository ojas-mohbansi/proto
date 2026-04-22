// Usage: !logs [lines]
const { sendReply, callApi } = require("../utils/helpers");

module.exports = {
  name: "logs",
  description: "Show recent log lines",
  async execute(sock, msg, args, db, config) {
    const n = Math.max(1, Math.min(30, parseInt(args[0]) || 15));
    const r = await callApi(`/logs/tail?filename=${encodeURIComponent("most recent")}&lines=${n}`, "GET", null, config);
    let body = (r.lines || []).join("\n");
    let notice = "";
    if (body.length > 3500) { body = body.slice(-3500); notice = "\n…(truncated)"; }
    await sendReply(sock, msg, `*Recent logs* (${r.file})\n\`\`\`\n${body}${notice}\n\`\`\``);
  },
};
