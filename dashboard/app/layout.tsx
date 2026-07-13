import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CIOTX — AI-Powered Code Security",
  description: "Find vulnerabilities before attackers do. AI agents that read every line, trace data across files, and report only what they can prove.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg-base text-text-primary font-sans antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
