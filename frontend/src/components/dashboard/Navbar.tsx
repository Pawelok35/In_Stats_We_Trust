"use client";

import { Bell, Menu } from "lucide-react";
import { useState } from "react";

import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex w-full items-center justify-between gap-4 border-b border-white/60 bg-white/70 px-6 py-4 backdrop-blur-xl dark:border-white/10 dark:bg-[#141934]/70">
      <div className="flex items-center gap-3">
        <button
          className="rounded-full border border-white/50 p-2 text-slate-600 transition hover:bg-white/70 dark:border-white/10 dark:text-white/70 dark:hover:bg-white/5"
          onClick={() => setOpen(!open)}
        >
          <Menu size={18} />
        </button>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
            In Stats We Trust
          </p>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
            Weather Scale Command Center
          </h1>
        </div>
      </div>

      <nav className="hidden items-center gap-6 text-sm font-medium text-slate-600 dark:text-white/70 md:flex">
        <span className="text-primary">Dashboard</span>
        <span className="hover:text-primary transition-colors">Reports</span>
        <span className="hover:text-primary transition-colors">Settings</span>
      </nav>

      <div className="flex items-center gap-4">
        <ThemeToggle />
        <button className="rounded-full border border-white/60 p-2 text-slate-500 transition hover:bg-white hover:text-primary dark:border-white/10 dark:text-white/70 dark:hover:bg-white/10">
          <Bell size={18} />
        </button>
        <div className="h-10 w-10 rounded-full border border-white/60 bg-gradient-to-br from-primary/80 via-emerald-400 to-indigo-600 shadow-inner dark:border-white/10" />
      </div>
    </header>
  );
}
