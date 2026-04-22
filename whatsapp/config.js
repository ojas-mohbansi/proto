// WhatsApp bot configuration. Edit values to suit your setup.
module.exports = {
  // Paste a base64 session string here to skip the QR pairing flow,
  // or leave empty to scan a QR code on first run.
  sessionID: process.env.WA_SESSION_ID || "",

  botName: process.env.WA_BOT_NAME || "Proto",
  ownerName: process.env.WA_OWNER_NAME || "Owner",
  // Full international number WITHOUT plus sign followed by @s.whatsapp.net.
  // Example: "919876543210@s.whatsapp.net"
  ownerNumber: process.env.WA_OWNER_NUMBER || "",

  prefix: process.env.WA_PREFIX || "!",
  // false: only the owner can use commands. true: anyone can.
  publicMode: (process.env.WA_PUBLIC_MODE || "false") === "true",
  autoRead: true,
  autoStatus: false,

  // FastAPI backend URL.
  agentApiBase: process.env.AGENT_API_BASE || "http://localhost:8000",

  commandDescriptions: {
    status: "Show current agent status",
    tasks: "List all tasks (!tasks [limit])",
    tree: "Show task tree",
    goal: "Set a new goal (!goal <text>)",
    logs: "Show recent log lines (!logs [n])",
    memory: "Search agent memory (!memory <query>)",
    pause: "Pause the agent (owner only)",
    resume: "Resume the agent (owner only)",
    stats: "Show combined agent / task / memory stats",
    help: "Show this help",
  },
};
