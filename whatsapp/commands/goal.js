// Usage: !goal <new goal text>
const { sendReply, callApi } = require("../utils/helpers");

module.exports = {
  name: "goal",
  description: "Set a new goal for the agent",
  async execute(sock, msg, args, db, config) {
    if (!args.length) return sendReply(sock, msg, `Usage: ${config.prefix}goal <new goal text>`);
    const goal = args.join(" ");
    try {
      const r = await callApi("/agent/goal", "POST", { goal }, config);
      await sendReply(sock, msg, `New goal set:\n${r.goal}`);
    } catch (e) {
      await sendReply(sock, msg, `Could not set goal: ${e.message}`);
    }
  },
};
