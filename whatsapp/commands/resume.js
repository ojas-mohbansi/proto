// Usage: !resume
const { sendReply, callApi, isOwner } = require("../utils/helpers");

module.exports = {
  name: "resume",
  description: "Resume the agent",
  async execute(sock, msg, args, db, config) {
    if (!isOwner(msg, config)) return sendReply(sock, msg, "Permission denied.");
    await callApi("/agent/resume", "POST", {}, config);
    await sendReply(sock, msg, "Agent has been resumed.");
  },
};
