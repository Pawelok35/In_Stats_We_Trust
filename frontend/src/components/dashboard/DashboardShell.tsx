"use client";

import { useEffect, useMemo, useState } from "react";

import type { WeatherPick } from "@/data/weather-picks";
import type { MatchupSummary, WeekIdentifier } from "@/lib/reports";
import type { ParsedReport } from "@/lib/markdown-parser";
import { cn } from "@/lib/utils";
import { weatherPicks as defaultPicks } from "@/data/weather-picks";

import { Navbar } from "./Navbar";
import { KpiRow } from "./KpiRow";
import { WeatherScaleTable } from "./WeatherScaleTable";
import { GameSummaryCard } from "./GameSummaryCard";
import { MatchupCharts } from "./MatchupCharts";
import { InsightsCard } from "./InsightsCard";
import { DetailedStatsGrid } from "./DetailedStatsGrid";
import { SectionsChartGrid } from "./SectionsChartGrid";

type Props = {
  initialWeeks: WeekIdentifier[];
  initialWeek?: WeekIdentifier;
  initialMatchups: MatchupSummary[];
  initialReport: ParsedReport | null;
  weatherPicks?: WeatherPick[];
};

export function DashboardShell({
  initialWeeks,
  initialWeek,
  initialMatchups,
  initialReport,
  weatherPicks = defaultPicks,
}: Props) {
  const defaultSeason = initialWeek?.season ?? initialWeeks[0]?.season ?? 2025;
  const defaultWeek = initialWeek?.week ?? initialWeeks[0]?.week ?? 1;

  const [season, setSeason] = useState(defaultSeason);
  const [week, setWeek] = useState(defaultWeek);
  const [matchups, setMatchups] = useState<MatchupSummary[]>(initialMatchups);
  const [selectedSlug, setSelectedSlug] = useState(initialMatchups[0]?.slug ?? "");
  const [report, setReport] = useState<ParsedReport | null>(initialReport);
  const [loadingReport, setLoadingReport] = useState(false);
  const [loadingMatchups, setLoadingMatchups] = useState(false);
  const [selectedPickId, setSelectedPickId] = useState<string | undefined>(undefined);

  const seasons = Array.from(new Set(initialWeeks.map((w) => w.season))).sort((a, b) => b - a);
  const weeksForSeason = initialWeeks
    .filter((w) => w.season === season)
    .map((w) => w.week)
    .sort((a, b) => b - a);

  useEffect(() => {
    let ignore = false;
    async function loadMatchups() {
      setLoadingMatchups(true);
      try {
        const res = await fetch(`/api/matchups?season=${season}&week=${week}`);
        const data = await res.json();
        if (ignore) return;
        const list: MatchupSummary[] = data.matchups ?? [];
        setMatchups(list);
        const newSlug = list[0]?.slug ?? "";
        setSelectedSlug(newSlug);
        if (newSlug) {
          await loadReport(season, week, newSlug);
        } else {
          setReport(null);
        }
      } finally {
        if (!ignore) setLoadingMatchups(false);
      }
    }
    loadMatchups();
    return () => {
      ignore = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [season, week]);

  async function loadReport(seasonValue: number, weekValue: number, slugValue: string) {
    setLoadingReport(true);
    try {
      const res = await fetch(
        `/api/report?season=${seasonValue}&week=${weekValue}&slug=${slugValue}`,
      );
      if (!res.ok) throw new Error("Failed to load report");
      const data = await res.json();
      setReport(data.report ?? null);
    } catch (error) {
      console.error(error);
      setReport(null);
    } finally {
      setLoadingReport(false);
    }
  }

  function handleMatchupChange(slug: string) {
    setSelectedSlug(slug);
    loadReport(season, week, slug);
  }

  function handlePickClick(pick: WeatherPick) {
    setSelectedPickId(pick.id);
    if (pick.season !== season || pick.week !== week) {
      setSeason(pick.season);
      setWeek(pick.week);
    } else {
      handleMatchupChange(pick.slug);
    }
  }

  const picksForWeek = useMemo(
    () => weatherPicks.filter((pick) => pick.season === season && pick.week === week),
    [season, week, weatherPicks],
  );

  const totalStake = picksForWeek.reduce((sum, pick) => sum + (pick.stake ?? 0), 0);
  const totalPicks = picksForWeek.filter((pick) => pick.stake !== null).length;

  const record = "73-31 (70%)"; // placeholder copy

  return (
    <div className="min-h-screen bg-transparent">
      <Navbar />

      <main className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 rounded-[32px] border border-white/60 bg-white/80 p-6 shadow-[0_25px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Season intelligence
              </p>
              <h2 className="text-4xl font-semibold text-slate-900 dark:text-white">
                Weather Scale Dashboard
              </h2>
              <p className="text-sm text-muted-foreground">
                Apple-grade UI for Weather Scale picks, PowerScore breakdowns and matchup edges.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <SelectControl
                label="Season"
                value={season}
                onChange={(value) => setSeason(Number(value))}
                options={seasons.map((s) => ({ label: `${s}`, value: s }))}
              />
              <SelectControl
                label="Week"
                value={week}
                onChange={(value) => setWeek(Number(value))}
                options={weeksForSeason.map((w) => ({ label: `Week ${w}`, value: w }))}
              />
              <SelectControl
                label="Game"
                value={selectedSlug}
                onChange={(value) => handleMatchupChange(String(value))}
                options={matchups.map((m) => ({ label: m.title, value: m.slug }))}
                disabled={loadingMatchups || matchups.length === 0}
              />
            </div>
          </div>

          <KpiRow totalPicks={totalPicks} stake={totalStake} record={record} />
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <WeatherScaleTable
            picks={picksForWeek.length ? picksForWeek : weatherPicks}
            selectedId={selectedPickId}
            onSelect={handlePickClick}
          />
          <GameSummaryCard report={report} pick={picksForWeek.find((p) => p.slug === selectedSlug)} />
        </div>

        <section className={cn("space-y-6", loadingReport && "opacity-60")}>
          <MatchupCharts report={report} />
        </section>

        <DetailedStatsGrid report={report} />

        <SectionsChartGrid report={report} />

        <InsightsCard report={report} />
      </main>
    </div>
  );
}

type SelectControlProps = {
  label: string;
  value: string | number;
  options: { label: string; value: string | number }[];
  onChange: (value: string | number) => void;
  disabled?: boolean;
};

function SelectControl({ label, value, options, onChange, disabled }: SelectControlProps) {
  return (
    <label className="flex flex-col text-xs font-semibold uppercase tracking-[0.3em] text-muted-foreground">
      {label}
      <select
        className="mt-1 rounded-2xl border border-white/60 bg-white/80 px-4 py-2 text-base font-medium text-slate-900 shadow-sm transition focus:ring-2 focus:ring-primary/50 dark:border-white/10 dark:bg-white/5 dark:text-white"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
