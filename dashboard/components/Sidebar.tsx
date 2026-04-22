"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, LayoutDashboard, ListTodo, ScrollText, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/logs", label: "Logs", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="fixed top-0 left-0 h-screen w-[220px] max-md:w-[64px] bg-card border-r border-border flex flex-col">
      <div className="px-4 py-5 max-md:px-2 flex items-center justify-center border-b border-border">
        <img
          src="/proto-wordmark.png"
          alt="Proto"
          className="max-md:hidden h-12 w-auto object-contain"
          style={{ filter: "invert(1) brightness(1.4) contrast(1.2)" }}
        />
        <img
          src="/proto-wordmark.png"
          alt="Proto"
          className="md:hidden h-9 w-9 object-contain"
          style={{ filter: "invert(1) brightness(1.4) contrast(1.2)" }}
        />
      </div>
      <div className="max-md:hidden px-5 pt-3 pb-4 text-[10px] font-accent uppercase tracking-[0.22em] text-[hsl(var(--accent))] text-center">
        The Proactive Agent
      </div>
      <nav className="flex-1 px-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 my-1 rounded-md text-sm",
                active ? "bg-accent text-foreground" : "text-muted-foreground hover:bg-accent/50",
              )}
            >
              <Icon size={18} />
              <span className="max-md:hidden">{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 text-xs text-muted-foreground max-md:hidden">v1.0.0</div>
    </aside>
  );
}
