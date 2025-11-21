"use client";

import { ArrowUpRight, Layers, Target } from "lucide-react";

type Props = {
  totalPicks: number;
  stake: number;
  record: string;
};

export function KpiRow({ totalPicks, stake, record }: Props) {
  const cards = [
    {
      title: "Signals this week",
      value: totalPicks,
      detail: "Weather Scale qualified picks",
      icon: <Layers size={18} />,
      accent: "from-primary/80 to-sky-400/80",
    },
    {
      title: "Total units deployed",
      value: `${stake.toFixed(1)}u`,
      detail: "Based on codename stake sizing",
      icon: <Target size={18} />,
      accent: "from-emerald-400/90 to-teal-500/80",
    },
    {
      title: "Season record",
      value: record,
      detail: "YTD Weather Scale performance",
      icon: <ArrowUpRight size={18} />,
      accent: "from-amber-300/80 to-orange-400/80",
    },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {cards.map((card) => (
        <div
          key={card.title}
          className="glass-card flex flex-col gap-2 rounded-[24px] p-4 text-sm text-slate-600 dark:text-white/70"
        >
          <div
            className={`inline-flex items-center gap-2 rounded-full bg-gradient-to-r ${card.accent} px-3 py-1 text-xs font-semibold text-white`}
          >
            {card.icon}
            {card.title}
          </div>
          <p className="text-3xl font-semibold text-slate-900 dark:text-white">{card.value}</p>
          <p className="text-xs text-muted-foreground">{card.detail}</p>
        </div>
      ))}
    </div>
  );
}
