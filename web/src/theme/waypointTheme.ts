import { defineTheme } from "@astryxdesign/core/theme";
import { neutralTheme } from "@astryxdesign/theme-neutral";

export const waypointTheme = defineTheme({
  name: "waypoint",
  extends: neutralTheme,
  typography: {
    scale: { base: 14, ratio: 1.2 },
    body: {
      family: "Inter",
      fallbacks:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    },
    heading: {
      family: "Inter",
      fallbacks:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      weights: { 1: "semibold", 2: "semibold", 3: "semibold" },
    },
    code: {
      family: "ui-monospace",
      fallbacks:
        '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
    },
  },
  motion: { fast: 110, medium: 220, slow: 500, ratio: 0.75 },
  radius: { base: 4, multiplier: 1 },
  tokens: {
    "--color-background-body": ["#f6f8fa", "#0d1117"],
    "--color-background-surface": ["#ffffff", "#161b22"],
    "--color-background-card": ["#ffffff", "#161b22"],
    "--color-background-popover": ["#ffffff", "#161b22"],
    "--color-background-muted": ["#f6f8fa", "#0d1117"],
    "--color-accent": ["#0969da", "#58a6ff"],
    "--color-accent-muted": ["#ddf4ff", "#1f2d3d"],
    "--color-text-primary": ["#1f2328", "#c9d1d9"],
    "--color-text-secondary": ["#59636e", "#8b949e"],
    "--color-text-accent": ["#0969da", "#58a6ff"],
    "--color-icon-accent": ["#0969da", "#58a6ff"],
    "--color-icon-primary": ["#1f2328", "#c9d1d9"],
    "--color-icon-secondary": ["#59636e", "#8b949e"],
    "--color-on-accent": "#ffffff",
    "--color-success": ["#1a7f37", "#3fb950"],
    "--color-warning": ["#9a6700", "#d29922"],
    "--color-error": ["#cf222e", "#ff7b72"],
    "--color-success-muted": ["#dafbe1", "#16351f"],
    "--color-warning-muted": ["#fff8c5", "#3d2f12"],
    "--color-error-muted": ["#ffebe9", "#3d1c20"],
    "--color-border": ["#d0d7de", "#30363d"],
    "--color-border-emphasized": ["#afb8c1", "#484f58"],
  },
  components: {
    button: {
      base: { fontWeight: "600" },
    },
    section: {
      base: { borderRadius: "6px" },
    },
    "file-input": {
      base: { borderRadius: "6px" },
    },
  },
});

export type ThemeMode = "light" | "dark" | "system";
