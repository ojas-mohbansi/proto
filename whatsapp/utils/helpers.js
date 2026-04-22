const fetch = require("node-fetch");

function getBody(msg) {
  const m = msg.message || {};
  return (
    m.conversation ||
    (m.extendedTextMessage && m.extendedTextMessage.text) ||
    (m.imageMessage && m.imageMessage.caption) ||
    (m.videoMessage && m.videoMessage.caption) ||
    ""
  );
}

async function sendReply(sock, msg, text) {
  try {
    await sock.sendMessage(msg.key.remoteJid, { text }, { quoted: msg });
  } catch (e) {
    console.error("sendReply error:", e.message);
  }
}

async function isAdmin(sock, msg) {
  try {
    const meta = await sock.groupMetadata(msg.key.remoteJid);
    const me = msg.key.participant;
    return meta.participants.some((p) => p.id === me && (p.admin === "admin" || p.admin === "superadmin"));
  } catch {
    return false;
  }
}

function isOwner(msg, config) {
  const sender = msg.key.participant || msg.key.remoteJid;
  return sender === config.ownerNumber;
}

async function callApi(endpoint, method = "GET", body = null, config) {
  const url = config.agentApiBase + endpoint;
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== null) opts.body = typeof body === "string" ? body : JSON.stringify(body);
  const r = await fetch(url, opts);
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`HTTP ${r.status}: ${text}`);
  }
  return r.json();
}

const STATUS_EMOJI = { DONE: "[OK]", ACTIVE: "[*]", PENDING: "[ ]", FAILED: "[X]", BLOCKED: "[-]" };

function formatTask(t) {
  const id = (t.id || "").slice(0, 8);
  const goal = (t.goal || "").slice(0, 60);
  const sym = STATUS_EMOJI[t.status] || "[?]";
  return `${sym} ${id}  ${goal}  (att=${t.attempts || 0})`;
}

function formatStatus(s) {
  return [
    `*Agent*: ${s.status}${s.paused ? " (paused)" : ""}`,
    `*Goal*: ${s.goal || "—"}`,
    `*Current task*: ${s.current_task_id || "—"}`,
    `*Done*: ${s.tasks_completed}   *Failed*: ${s.tasks_failed}`,
    `*LLM*: ${s.llm_provider || "?"} (${s.llm_model || "?"}) — ${s.ollama_available ? "online" : "offline"}`,
    `*Last heartbeat*: ${s.last_heartbeat || "—"}`,
  ].join("\n");
}

module.exports = { getBody, sendReply, isAdmin, isOwner, callApi, formatTask, formatStatus };
