// Usage: !tree
const { sendReply, callApi } = require("../utils/helpers");

module.exports = {
  name: "tree",
  description: "Show task tree",
  async execute(sock, msg, args, db, config) {
    const r = await callApi("/tasks/tree", "GET", null, config);
    const tree = (r.tree || "").trim();
    if (!tree || tree === "(empty)") return sendReply(sock, msg, "No tasks in the planner.");
    await sendReply(sock, msg, "*Task Tree*\n```\n" + tree + "\n```");
  },
};
