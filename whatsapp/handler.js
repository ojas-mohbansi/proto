const fs = require("fs");
const path = require("path");
const { getBody, sendReply, isOwner } = require("./utils/helpers");

const commands = new Map();
const cmdDir = path.join(__dirname, "commands");
for (const file of fs.readdirSync(cmdDir).filter((f) => f.endsWith(".js"))) {
  const cmd = require(path.join(cmdDir, file));
  if (cmd && cmd.name && typeof cmd.execute === "function") {
    commands.set(cmd.name, cmd);
    console.log(`[handler] loaded command: ${cmd.name}`);
  }
}

async function handleMessage(sock, upsert, db, config) {
  if (upsert.type !== "notify") return;
  for (const msg of upsert.messages) {
    if (!msg.message || msg.key.fromMe) continue;
    const sender = msg.key.participant || msg.key.remoteJid;

    if (config.autoRead) {
      try { await sock.readMessages([msg.key]); } catch {}
    }

    if (!config.publicMode && !isOwner(msg, config)) continue;

    const body = getBody(msg).trim();
    if (!body.startsWith(config.prefix)) continue;

    const parts = body.slice(config.prefix.length).trim().split(/\s+/);
    const name = (parts.shift() || "").toLowerCase();
    const args = parts;

    const cmd = commands.get(name);
    if (!cmd) {
      await sendReply(sock, msg, `Unknown command: ${name}. Try ${config.prefix}help`);
      continue;
    }

    try { await sock.sendPresenceUpdate("composing", msg.key.remoteJid); } catch {}
    try {
      await cmd.execute(sock, msg, args, db, config);
    } catch (e) {
      console.error(`[cmd ${name}] error:`, e);
      await sendReply(sock, msg, `Error running ${name}: ${e.message}`);
    } finally {
      try { await sock.sendPresenceUpdate("paused", msg.key.remoteJid); } catch {}
    }
  }
}

module.exports = { handleMessage, commands };
