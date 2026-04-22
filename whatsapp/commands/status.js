// Usage: !status
const { sendReply, callApi, formatStatus } = require("../utils/helpers");

module.exports = {
  name: "status",
  description: "Show current agent status",
  async execute(sock, msg, args, db, config) {
    try {
      const s = await callApi("/agent/status", "GET", null, config);
      await sendReply(sock, msg, formatStatus(s));
    } catch (e) {
      await sendReply(sock, msg, `Could not reach agent API: ${e.message}`);
    }
  },
};
