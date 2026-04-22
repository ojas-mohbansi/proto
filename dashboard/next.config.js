/** @type {import('next').NextConfig} */
const API_BASE = process.env.AGENT_API_BASE || "http://localhost:8000";
// Disable proxy rewrites when paths are served by an external reverse proxy
// (e.g. inside Replit). Set NEXT_PUBLIC_API_PATH=/agent-api in that case.
const DISABLE_REWRITES = !!process.env.NEXT_PUBLIC_API_PATH;

module.exports = {
  async rewrites() {
    if (DISABLE_REWRITES) return [];
    return [{ source: "/api/:path*", destination: `${API_BASE}/:path*` }];
  },
};
