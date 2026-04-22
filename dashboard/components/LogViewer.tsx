"use client";

function colorOf(line: string) {
  if (/ERROR|CRITICAL/i.test(line)) return "text-red-400";
  if (/WARN|WARNING/i.test(line)) return "text-yellow-300";
  if (/SUCCESS/i.test(line)) return "text-green-400";
  return "text-muted-foreground";
}

export default function LogViewer({ content }: { content: string[] }) {
  return (
    <div className="rounded-lg border border-border bg-card overflow-auto" style={{ maxHeight: 600 }}>
      <pre className="font-mono text-xs">
        {content.map((line, i) => (
          <div key={i} className="flex">
            <span className="text-muted-foreground/60 px-3 select-none w-14 text-right">{i + 1}</span>
            <span className={`flex-1 px-2 ${colorOf(line)}`}>{line || " "}</span>
          </div>
        ))}
      </pre>
    </div>
  );
}
