// frontend/components/layout/ThemeToggle.tsx
"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

const STORAGE_KEY = "qa-theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  // 初期化：localStorage or システム設定から
  useEffect(() => {
    if (typeof window === "undefined") return;

    const stored = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (stored === "light" || stored === "dark") {
      applyTheme(stored);
      setTheme(stored);
      return;
    }

    const prefersDark = window.matchMedia?.(
      "(prefers-color-scheme: dark)"
    ).matches;
    const initial: Theme = prefersDark ? "dark" : "light";
    applyTheme(initial);
    setTheme(initial);
  }, []);

  const applyTheme = (t: Theme) => {
    if (typeof document === "undefined") return;
    document.documentElement.setAttribute("data-theme", t);
    window.localStorage.setItem(STORAGE_KEY, t);
  };

  const toggle = () => {
    const next: Theme = theme === "light" ? "dark" : "light";
    setTheme(next);
    applyTheme(next);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className="qa-theme-toggle"
      aria-label="Toggle theme"
    >
      {theme === "light" ? "🌙" : "☀️"}
    </button>
  );
}
