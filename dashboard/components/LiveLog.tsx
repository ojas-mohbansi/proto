"use client";
import { useEffect, useRef, useState } from "react";

const MAX_LINES = 500;

function colorOf(line: string) {
  if (/ERROR|CRITICAL/i.test(line)) return "text-red-400";
  if (/WARN|WARNING/i.test(line)) return "text-yellow-300";
  if (/SUCCESS/i.test(line)) return "text-green-400";
  if (/INFO/i.test(line)) return "text-foreground";
  return "text-muted-foreground";
}

export default function LiveLog() {
  const [lines, setLines] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const stickyRef = useRef(true);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout>;
    let killed = false;

    const connect = () => {
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      const wsPath = process.env.NEXT_PUBLIC_WS_PATH || "/ws";
      ws = new WebSocket(`${proto}//${location.host}${wsPath}/logs`);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!killed) timer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (ev) => {
        setLines((prev) => {
          const next = prev.concat(String(ev.data).split("\n"));
          return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next;
        });
      };
    };
    connect();
    return () => { killed = true; clearTimeout(timer); ws?.close(); };
  }, []);

  useEffect(() => {
    if (!stickyRef.current) return;
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight });
  }, [lines]);

  const onScroll = () => {
    const el = boxRef.current;
    if (!el) return;
    stickyRef.current = el.scrollTop + el.clientHeight >= el.scrollHeight - 20;
  };

  return (
    <div className="relative rounded-lg border border-border bg-card">
      <div className="absolute top-2 right-2 text-xs">
        {connected ? (
          <span className="px-2 py-0.5 bg-green-600/30 text-green-300 rounded">connected</span>
        ) : (
          <span className="px-2 py-0.5 bg-yellow-600/30 text-yellow-300 rounded">reconnecting…</span>
        )}
      </div>
      <div
        ref={boxRef}
        onScroll={onScroll}
        className="h-80 overflow-auto p-3 font-mono text-xs space-y-0.5"
      >
        {lines.map((l, i) => (
          <div key={i} className={colorOf(l)}>{l}</div>
        ))}
      </div>
    </div>
  );
}
