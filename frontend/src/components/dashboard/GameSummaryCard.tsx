"use client";

import { ArrowRight, Compass, Trophy } from "lucide-react";

import type { ParsedReport } from "@/lib/markdown-parser";
import type { WeatherPick } from "@/data/weather-picks";
import { cn } from "@/lib/utils";

type Props = {
  report?: ParsedReport | null;
  pick?: WeatherPick | null;
};

export function GameSummaryCard({ report, pick }: Props) {
  const title = report ? `${report.teams.home} vs ${report.teams.away}` : "Select a matchup";
  const subtitle = pick ? `${pick.codename} · ${pick.direction}` : "Choose a Weather Scale signal";

  return (
    <div className="glass-card flex flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Selected game</p>
          <h3 className="text-2xl font-semibold text-slate-900 dark:text-white">{title}</h3>
        </div>
        <span className="text-sm font-medium text-primary">{subtitle}</span>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          icon={<Compass size={16} />}
          label="Model favorite"
          value={pick?.direction ?? report?.modelOutlook.favorite ?? "—"}
          accent="from-primary/80 to-blue-400/70"
        />
        <MetricCard
          icon={<ArrowRight size={16} />}
          label="Model spread"
          value={
            report?.modelOutlook.spread !== undefined
              ? `${report.modelOutlook.spread.toFixed(1)} pts`
              : "—"
          }
          accent="from-emerald-400/80 to-teal-500/80"
        />
        <MetricCard
          icon={<Trophy size={16} />}
          label="Win probabilities"
          value={
            report?.modelOutlook.homeWin !== undefined &&
            report?.modelOutlook.awayWin !== undefined
              ? `${report.modelOutlook.homeWin.toFixed(0)}% / ${report.modelOutlook.awayWin.toFixed(
                  0,
                )}%`
              : "—"
          }
          accent="from-amber-300/80 to-orange-400/80"
        />
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-white/70 bg-white/90 p-4 text-sm shadow-inner dark:border-white/10 dark:bg-white/5",
      )}
    >
      <div
        className={cn(
          "mb-3 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium text-white",
          "bg-gradient-to-r",
          accent,
        )}
      >
        {icon}
        {label}
      </div>
      <p className="text-2xl font-semibold text-slate-900 dark:text-white">{value}</p>
    </div>
  );
}
