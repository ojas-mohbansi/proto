const fs = require("fs");
const path = require("path");
const pino = require("pino");
const { Boom } = require("@hapi/boom");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  DisconnectReason,
  makeCacheableSignalKeyStore,
} = require("@whiskeysockets/baileys");

const config = require("./config");
const db = require("./database");
const { handleMessage } = require("./handler");

const SESSION_DIR = path.join(__dirname, "session");

function restoreSession() {
  if (!config.sessionID) return;
  if (!fs.existsSync(SESSION_DIR)) fs.mkdirSync(SESSION_DIR, { recursive: true });
  const credsPath = path.join(SESSION_DIR, "creds.json");
  if (!fs.existsSync(credsPath)) {
    try {
      const decoded = Buffer.from(config.sessionID, "base64").toString("utf-8");
      fs.writeFileSync(credsPath, decoded);
      console.log("[session] restored from base64 sessionID");
    } catch (e) {
      console.error("[session] failed to restore:", e.message);
    }
  }
}

async function startBot() {
  restoreSession();
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
  const { version } = await fetchLatestBaileysVersion();
  const logger = pino({ level: "silent" });

  const sock = makeWASocket({
    version,
    logger,
    printQRInTerminal: !config.sessionID,
    auth: { creds: state.creds, keys: makeCacheableSignalKeyStore(state.keys, logger) },
    browser: [config.botName, "Chrome", "1.0.0"],
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (u) => {
    const { connection, lastDisconnect } = u;
    if (connection === "open") {
      console.log(`[bot] online as ${config.botName}`);
    } else if (connection === "close") {
      const code = lastDisconnect?.error instanceof Boom ? lastDisconnect.error.output.statusCode : 0;
      if (code === DisconnectReason.loggedOut) {
        console.log("[bot] logged out; deleting session");
        try { fs.rmSync(SESSION_DIR, { recursive: true, force: true }); } catch {}
        process.exit(0);
      } else {
        console.log(`[bot] disconnected (${code}); reconnecting in 5s`);
        setTimeout(startBot, 5000);
      }
    }
  });

  sock.ev.on("messages.upsert", (upsert) => handleMessage(sock, upsert, db, config));
}

startBot().catch((e) => console.error("[bot] startBot error:", e));
