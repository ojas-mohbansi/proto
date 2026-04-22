import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Proto — The Proactive Agent",
  description: "Self-hosted autonomous AI agent dashboard.",
  icons: { icon: "/proto-wordmark.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-[220px] max-md:ml-[64px] p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
