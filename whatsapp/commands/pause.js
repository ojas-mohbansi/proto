// Usage: !pause
const { sendReply, callApi, isOwner } = require("../utils/helpers");

module.exports = {
  name: "pause",
  description: "Pause the agent",
  async execute(sock, msg, args, db, config) {
    if (!isOwner(msg, config)) return sendReply(sock, msg, "Permission denied.");
    await callApi("/agent/pause", "POST", {}, config);
    await sendReply(sock, msg, "Agent will pause before its next task execution.");
  },
};
