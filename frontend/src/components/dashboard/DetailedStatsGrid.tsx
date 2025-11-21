"use client";

import type { ParsedReport } from "@/lib/markdown-parser";

type Section = {
  key: string;
  title: string;
  description: string;
  accent: string;
  empty: string;
};

const SECTIONS: Section[] = [
  {
    key: "PowerScore Summary",
    title: "PowerScore Summary",
    description: "Weighted blend of Core12 + matchup modifiers.",
    accent: "from-primary/90 to-cyan-400/70",
    empty: "PowerScore summary missing from report.",
  },
  {
    key: "Situational Edges",
    title: "Situational Edges",
    description: "Tempo, rest, travel and market context.",
    accent: "from-amber-300/90 to-orange-400/80",
    empty: "No situational edge data.",
  },
  {
    key: "Matchup Edges",
    title: "Matchup Edges",
    description: "Binary edges across rush/pass and trenches.",
    accent: "from-violet-500/80 to-fuchsia-400/80",
    empty: "Matchup edge table not found.",
  },
];

export function DetailedStatsGrid({ report }: { report?: ParsedReport | null }) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {SECTIONS.map((section) => {
        const table = report?.tables[section.key];
        return (
          <article
            key={section.key}
            className="rounded-[28px] border border-white/60 bg-white/80 p-5 shadow-inner dark:border-white/10 dark:bg-white/5"
          >
            <p
              className={`inline-flex items-center rounded-full bg-gradient-to-r ${section.accent} px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white`}
            >
              {section.title}
            </p>
            <p className="mt-2 text-xs text-muted-foreground">{section.description}</p>
            <div className="mt-4 space-y-3 text-sm text-slate-700 dark:text-white/80">
              {table && table.rows.length > 0 ? (
                table.rows.slice(0, 4).map((row, idx) => (
                  <div
                    key={`${section.key}-${idx}`}
                    className="rounded-2xl border border-white/70 bg-white/80 px-3 py-2 shadow-sm dark:border-white/10 dark:bg-white/10"
                  >
                    <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      {row[0]}
                    </div>
                    <p className="text-base font-semibold">{row.slice(1).join(" · ")}</p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground">{section.empty}</p>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
