import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "bg-base": "#0A0A0A",
        "bg-surface": "#141414",
        "bg-elevated": "#1A1A1A",
        "bg-hover": "#222222",
        "bg-active": "#2A2A2A",
        "border-subtle": "#1F1F1F",
        "border-default": "#2E2E2E",
        "border-strong": "#3A3A3A",
        "text-primary": "#EDEDED",
        "text-secondary": "#888888",
        "text-tertiary": "#5A5A5A",
        accent: "#FAFAFA",
        "accent-hover": "#FFFFFF",
        "accent-text": "#0A0A0A",
        "severity-critical": "#E5484D",
        "severity-high": "#F97316",
        "severity-medium": "#F5A623",
        "severity-low": "#5E9EFF",
        "severity-info": "#888888",
        "status-success": "#10B981",
        "status-warning": "#F59E0B",
        "status-error": "#EF4444",
      },
      fontFamily: {
        sans: ["Geist", "Inter", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "JetBrains Mono", "monospace"],
      },
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
      },
      spacing: {
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "6": "24px",
        "8": "32px",
        "12": "48px",
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        lg: "8px",
        xl: "12px",
      },
      boxShadow: {
        md: "0 1px 2px rgba(0,0,0,0.5)",
        lg: "0 4px 12px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
};

export default config;
