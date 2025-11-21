"use client";

import { cn } from "@/lib/utils";
import type { WeatherPick } from "@/data/weather-picks";

const CODE_COLORS: Record<WeatherPick["codename"], string> = {
  "Ultimate Supercell": "from-orange-500 to-pink-500 text-white",
  Supercell: "bg-gradient-to-br from-blue-600/90 to-sky-400/80 text-white",
  Vortex: "bg-gradient-to-br from-slate-900/85 to-slate-700/85 text-white",
  Cyclone: "bg-gradient-to-br from-emerald-500/90 to-teal-400/80 text-white",
  Gale: "bg-gradient-to-br from-indigo-500/80 to-blue-400/70 text-white",
  Breeze: "bg-gradient-to-br from-cyan-400/80 to-sky-300/70 text-slate-900",
  Calm: "bg-slate-200 text-slate-900 dark:bg-white/10 dark:text-white",
};

type Props = {
  picks: WeatherPick[];
  selectedId?: string;
  onSelect: (pick: WeatherPick) => void;
};

export function WeatherScaleTable({ picks, selectedId, onSelect }: Props) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Signal stack</p>
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">
            Weather Scale Picks
          </h2>
        </div>
        <div className="text-xs text-muted-foreground">click a row to preview report</div>
      </div>

      <div className="mt-6 overflow-hidden rounded-3xl border border-white/70 dark:border-white/10">
        <table className="w-full">
          <thead className="bg-white/90 text-xs uppercase tracking-[0.3em] text-slate-500 dark:bg-white/5 dark:text-white/60">
            <tr>
              <th className="px-4 py-3 text-left">Codename</th>
              <th className="px-4 py-3 text-left">Rating</th>
              <th className="px-4 py-3 text-left">Stake</th>
              <th className="px-4 py-3 text-left">Matchup</th>
              <th className="px-4 py-3 text-left">Models</th>
            </tr>
          </thead>
          <tbody>
            {picks.map((pick) => (
              <tr
                key={pick.id}
                className={cn(
                  "cursor-pointer border-t border-white/60 bg-white/80 text-sm transition dark:border-white/5 dark:bg-white/5",
                  selectedId === pick.id && "bg-gradient-to-r from-primary/5 to-transparent",
                  "hover:bg-gradient-to-r hover:from-primary/10 hover:to-transparent dark:hover:from-white/10",
                )}
                onClick={() => onSelect(pick)}
              >
                <td className="px-4 py-4">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
                      CODE_COLORS[pick.codename],
                    )}
                  >
                    {pick.codename}
                  </span>
                </td>
                <td className="px-4 py-4 font-semibold">
                  {pick.rating ? pick.rating.toFixed(2) : "—"}
                </td>
                <td className="px-4 py-4">{pick.stake ? `${pick.stake.toFixed(1)}u` : "—"}</td>
                <td className="px-4 py-4">
                  <div className="font-medium text-slate-900 dark:text-white">
                    {pick.matchup}
                  </div>
                  <p className="text-xs text-muted-foreground">{pick.direction}</p>
                </td>
                <td className="px-4 py-4 text-xs text-muted-foreground">{pick.badge}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
