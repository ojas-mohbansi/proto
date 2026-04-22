"use client";
import { useEffect, useState } from "react";
import { getLogFiles, getLogTail } from "@/lib/api";
import type { LogFile } from "@/lib/types";
import LogViewer from "@/components/LogViewer";

export default function LogsPage() {
  const [files, setFiles] = useState<LogFile[]>([]);
  const [filename, setFilename] = useState("most recent");
  const [lines, setLines] = useState(200);
  const [content, setContent] = useState<string[]>([]);

  const refresh = async () => {
    if (!files.length) { setContent([]); return; }
    try {
      const r = await getLogTail(filename, lines);
      setContent(r.lines);
    } catch {
      setContent([]);
    }
  };

  useEffect(() => { (async () => {
    try {
      const fs = await getLogFiles(); setFiles(fs);
      if (fs.length) setFilename(fs[0].name);
    } catch { setFiles([]); }
  })(); }, []);

  useEffect(() => { if (filename && files.length) refresh(); /* eslint-disable-next-line */ }, [filename, files.length]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Logs</h1>
      <div className="flex flex-wrap gap-2 items-center">
        <select className="bg-card border border-border rounded px-2 py-1.5" value={filename} onChange={(e) => setFilename(e.target.value)}>
          {files.map(f => <option key={f.name} value={f.name}>{f.name} ({Math.round(f.size/1024)} KB)</option>)}
        </select>
        <input type="number" min={10} max={10000} value={lines} onChange={(e) => setLines(parseInt(e.target.value || "200"))} className="w-24 bg-card border border-border rounded px-2 py-1.5" />
        <button className="px-3 py-1.5 rounded bg-secondary" onClick={refresh}>Refresh</button>
        <a className="px-3 py-1.5 rounded bg-primary text-primary-foreground" href={`${process.env.NEXT_PUBLIC_API_PATH || "/api"}/logs/download/${encodeURIComponent(filename)}`}>Download</a>
      </div>
      <LogViewer content={content} />
    </div>
  );
}
