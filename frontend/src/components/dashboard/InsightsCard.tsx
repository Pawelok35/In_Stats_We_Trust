"use client";

import type { ParsedReport } from "@/lib/markdown-parser";

export function InsightsCard({ report }: { report?: ParsedReport | null }) {
  const insights = buildInsights(report);

  return (
    <div className="glass-card p-6">
      <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">AI insights</p>
      <h3 className="text-2xl font-semibold text-slate-900 dark:text-white">Weekly read</h3>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {insights.map((insight) => (
          <div
            key={insight.title}
            className="rounded-3xl border border-white/60 bg-white/80 p-4 text-sm text-slate-700 shadow-inner dark:border-white/10 dark:bg-white/5 dark:text-white/80"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {insight.title}
            </p>
            <p className="mt-2 text-base font-semibold">{insight.value}</p>
            <p className="text-xs text-muted-foreground">{insight.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function buildInsights(report?: ParsedReport | null) {
  if (!report) {
    return [
      { title: "Status", value: "Waiting for selection", detail: "Choose a matchup above." },
    ];
  }
  const outlook = report.modelOutlook;
  return [
    {
      title: "EPA edge",
      value: outlook.favorite ?? "Balanced",
      detail: "Model favorite derived from PowerScore spread.",
    },
    {
      title: "Win probability",
      value:
        outlook.homeWin && outlook.awayWin
          ? `${outlook.homeWin.toFixed(0)}% / ${outlook.awayWin.toFixed(0)}%`
          : "N/A",
      detail: `${report.teams.home} vs ${report.teams.away}`,
    },
    {
      title: "Spread delta",
      value:
        outlook.spread !== undefined ? `${outlook.spread.toFixed(1)} pts` : "Waiting for data",
      detail: "Difference between model and market.",
    },
    {
      title: "Confidence",
      value: outlook.favorite ? "Weather Scale aligned" : "Check inputs",
      detail: "Signal ties back to pick codename + model spread.",
    },
  ];
}
