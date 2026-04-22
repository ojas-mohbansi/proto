// Usage: !help
const { sendReply } = require("../utils/helpers");

module.exports = {
  name: "help",
  description: "Show all commands",
  async execute(sock, msg, args, db, config) {
    const lines = [`*${config.botName}* — prefix \`${config.prefix}\``, ""];
    for (const [name, desc] of Object.entries(config.commandDescriptions)) {
      lines.push(`${config.prefix}${name} — ${desc}`);
    }
    await sendReply(sock, msg, lines.join("\n"));
  },
};
