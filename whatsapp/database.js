const fs = require("fs");
const path = require("path");

const DB_PATH = path.join(__dirname, "db.json");

function _read() {
  try { return JSON.parse(fs.readFileSync(DB_PATH, "utf-8")); }
  catch { return { warns: {}, banned: {} }; }
}
function _write(d) { fs.writeFileSync(DB_PATH, JSON.stringify(d, null, 2)); }

let state = _read();

module.exports = {
  getWarns(jid) { return state.warns[jid] || 0; },
  addWarn(jid) { state.warns[jid] = (state.warns[jid] || 0) + 1; _write(state); return state.warns[jid]; },
  clearWarns(jid) { delete state.warns[jid]; _write(state); },
  isBanned(jid) { return !!state.banned[jid]; },
  ban(jid) { state.banned[jid] = true; _write(state); },
  unban(jid) { delete state.banned[jid]; _write(state); },
};
