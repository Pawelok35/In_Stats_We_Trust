"use client";

import { Activity, Ban, CheckCircle2, Filter, GitCommit, Target } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OperationalPick, PickDecision } from "@/lib/pick-types";

type Props = {
  picks: OperationalPick[];
  loading?: boolean;
  selectedSlug?: string;
  onSelect: (pick: OperationalPick) => void;
};

const decisionLabels: Record<PickDecision | "all", string> = {
  all: "All",
  bet: "Bet",
  lean: "Lean",
  avoid: "Avoid",
  "no bet": "No bet",
};

const decisionStyles: Record<PickDecision, string> = {
  bet: "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  lean: "border-blue-500/40 bg-blue-500/10 text-blue-700 dark:text-blue-300",
  avoid: "border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-300",
  "no bet": "border-slate-400/40 bg-slate-500/10 text-slate-600 dark:text-slate-300",
};

export function OperationalPicksTable({ picks, loading, selectedSlug, onSelect }: Props) {
  const [statusFilter, setStatusFilter] = useState("active");
  const [decisionFilter, setDecisionFilter] = useState<PickDecision | "all">("all");

  const visiblePicks = useMemo(() => {
    return picks.filter((pick) => {
      const statusOk =
        statusFilter === "all" ||
        (statusFilter === "active"
          ? pick.variantStatus === "champion" || pick.variantStatus === "challenger"
          : pick.variantStatus === statusFilter);
      const decisionOk = decisionFilter === "all" || pick.decision === decisionFilter;
      return statusOk && decisionOk;
    });
  }, [picks, statusFilter, decisionFilter]);

  const stats = useMemo(() => {
    return {
      total: visiblePicks.length,
      bets: visiblePicks.filter((pick) => pick.decision === "bet").length,
      leans: visiblePicks.filter((pick) => pick.decision === "lean").length,
      variants: new Set(visiblePicks.map((pick) => pick.variant)).size,
    };
  }, [visiblePicks]);

  return (
    <section className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
            <Activity className="h-4 w-4" />
            Operational Board
          </div>
          <h2 className="mt-1 text-xl font-semibold text-foreground">Variant Pick Queue</h2>
        </div>

        <div className="grid grid-cols-4 gap-2 text-center text-xs">
          <Metric label="Shown" value={stats.total} />
          <Metric label="Bets" value={stats.bets} />
          <Metric label="Leans" value={stats.leans} />
          <Metric label="Variants" value={stats.variants} />
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <SegmentedFilter
          label="Status"
          value={statusFilter}
          options={[
            ["active", "Active"],
            ["champion", "Champion"],
            ["challenger", "Challenger"],
            ["experimental", "Experimental"],
            ["all", "All"],
          ]}
          onChange={setStatusFilter}
        />
        <SegmentedFilter
          label="Decision"
          value={decisionFilter}
          options={[
            ["all", decisionLabels.all],
            ["bet", decisionLabels.bet],
            ["lean", decisionLabels.lean],
            ["avoid", decisionLabels.avoid],
            ["no bet", decisionLabels["no bet"]],
          ]}
          onChange={(value) => setDecisionFilter(value as PickDecision | "all")}
        />
      </div>

      <div className="mt-4 overflow-x-auto rounded-lg border border-border">
        <table className="w-full min-w-[980px] text-sm">
          <thead className="bg-secondary/70 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-3 text-left">Decision</th>
              <th className="px-3 py-3 text-left">Matchup</th>
              <th className="px-3 py-3 text-left">Variant</th>
              <th className="px-3 py-3 text-right">Conf</th>
              <th className="px-3 py-3 text-right">Edge</th>
              <th className="px-3 py-3 text-left">Pick</th>
              <th className="px-3 py-3 text-left">Version</th>
            </tr>
          </thead>
          <tbody>
            {visiblePicks.map((pick) => (
              <tr
                key={pick.id}
                className={cn(
                  "cursor-pointer border-t border-border bg-card transition hover:bg-secondary/50",
                  selectedSlug === pick.slug && "bg-primary/5",
                )}
                onClick={() => onSelect(pick)}
              >
                <td className="px-3 py-3">
                  <DecisionBadge decision={pick.decision} />
                </td>
                <td className="px-3 py-3">
                  <div className="font-medium text-foreground">{pick.matchup}</div>
                  <div className="text-xs text-muted-foreground">
                    {pick.tag} · {pick.window ?? "season"}
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="font-medium">{pick.variant}</div>
                  <div className="text-xs capitalize text-muted-foreground">{pick.variantStatus}</div>
                </td>
                <td className="px-3 py-3 text-right font-mono">
                  {formatNumber(pick.confidence, 1)}
                </td>
                <td className="px-3 py-3 text-right font-mono">
                  {formatSigned(pick.edgeVsLine)}
                </td>
                <td className="px-3 py-3">
                  <div className="font-medium">{pick.modelWinner}</div>
                  <div className="text-xs text-muted-foreground">
                    line {formatSigned(pick.handicap)}
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <GitCommit className="h-3.5 w-3.5" />
                    {pick.commitSha ? pick.commitSha.slice(0, 7) : "legacy"}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {pick.modelVersion ?? pick.variant}
                  </div>
                </td>
              </tr>
            ))}
            {!visiblePicks.length && (
              <tr>
                <td colSpan={7} className="px-3 py-10 text-center text-sm text-muted-foreground">
                  {loading ? "Loading picks..." : "No picks match the selected filters."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-secondary/50 px-3 py-2">
      <div className="text-base font-semibold text-foreground">{value}</div>
      <div className="text-[11px] uppercase text-muted-foreground">{label}</div>
    </div>
  );
}

function SegmentedFilter({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: [string, string][];
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1 text-xs font-semibold uppercase text-muted-foreground">
        <Filter className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="flex flex-wrap gap-1 rounded-md border border-border bg-secondary/40 p-1">
        {options.map(([optionValue, optionLabel]) => (
          <Button
            key={optionValue}
            type="button"
            variant={value === optionValue ? "default" : "ghost"}
            size="sm"
            className="h-7 rounded px-2 text-xs"
            onClick={() => onChange(optionValue)}
          >
            {optionLabel}
          </Button>
        ))}
      </div>
    </div>
  );
}

function DecisionBadge({ decision }: { decision: PickDecision }) {
  const Icon = decision === "avoid" ? Ban : decision === "bet" ? Target : CheckCircle2;
  return (
    <Badge className={cn("gap-1 rounded-md border px-2 py-1 capitalize", decisionStyles[decision])}>
      <Icon className="h-3.5 w-3.5" />
      {decision}
    </Badge>
  );
}

function formatNumber(value: number | null, digits = 1) {
  return value === null ? "n/a" : value.toFixed(digits);
}

function formatSigned(value: number | null) {
  if (value === null) return "n/a";
  return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
}
