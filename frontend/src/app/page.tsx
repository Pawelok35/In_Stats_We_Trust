import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { listAvailableWeeks, listMatchupsForWeek } from "@/lib/reports";

export default function Home() {
  const weeks = listAvailableWeeks();

  // No reports case – keep it simple and calm
  if (weeks.length === 0) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-background px-6 py-12">
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle>No reports found</CardTitle>
            <CardDescription>
              No generated matchup reports were found in
              <code className="ml-1 rounded bg-muted px-1.5 py-0.5 font-mono text-sm">
                data/reports/comparisons
              </code>
              . Once you build reports, they will appear here automatically.
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  const latest = weeks[0];
  const matchups = listMatchupsForWeek(latest.season, latest.week);

  return (
    <main className="min-h-screen bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        {/* HERO / TOP SECTION */}
<header className="space-y-8 text-center md:text-left">
  <div className="flex flex-wrap items-center justify-between gap-4">
    <Badge variant="outline" className="w-fit text-xs sm:text-sm">
      In Stats We Trust · NFL Analytics
    </Badge>
    <span className="text-xs text-muted-foreground">
      Core12 Engine · Season {latest.season}, Week {latest.week}
    </span>
  </div>

  <div className="grid gap-10 md:grid-cols-[minmax(0,2fr)_minmax(0,1.3fr)] md:items-center">
    <div className="space-y-6">
      <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl">
        Data. Models. Insights.
      </h1>
      <p className="max-w-xl text-lg text-gray-600">
        Predict games with confidence. In Stats We Trust transforms NFL data into powerful and transparent analytics – no hype, just numbers.
      </p>

      <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700 text-white">
        <Link href={`/weeks/${latest.season}/${latest.week}`}>Open NFL Dashboard</Link>
      </Button>
    </div>

    {/* MINI LIVE PREVIEW – LATEST WEEK */}
    <Card className="shadow-md border border-gray-200">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Latest Matchup Reports
        </CardTitle>
        <CardDescription>
          Generated from your comparison data.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {matchups.slice(0, 3).map((m) => (
          <div key={m.slug} className="flex items-center justify-between text-sm">
            <span className="font-medium text-gray-800">{m.title}</span>
            <Link
              href={`/reports/${latest.season}/${latest.week}/${m.slug}`}
              className="text-blue-600 hover:underline"
            >
              Open →
            </Link>
          </div>
        ))}
      </CardContent>
    </Card>
  </div>
</header>


        <Separator />

        {/* HOW IT WORKS SECTION */}
        <section id="how-it-works" className="bg-gray-50 py-16">

          <div className="space-y-2">
            <h2 className="text-2xl font-semibold uppercase tracking-[0.15em]">
              How it works
            </h2>
            <p className="max-w-2xl text-sm text-muted-foreground">
              ISWT connects your NFL data pipeline with a clear, opinion-free
              UI. Three simple layers: data in, model logic, actionable insight.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Card className="retro-frame">
              <CardHeader className="pb-3">
                <CardTitle className="retro-frame-title text-sm">
                  01 · Data
                </CardTitle>
                <CardDescription>
                  Play-by-play, Core12 metrics and weekly aggregates from your
                  backend pipeline.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  ISWT reads your generated reports and Core12 files – no manual
                  uploads, no spreadsheets.
                </p>
              </CardContent>
            </Card>

            <Card className="retro-frame">
              <CardHeader className="pb-3">
                <CardTitle className="retro-frame-title text-sm">
                  02 · Model
                </CardTitle>
                <CardDescription>
                  Transparent PowerScore and matchup logic – always explainable.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  PowerScore, Core12 and matchup reports are all derived from
                  the same deterministic pipeline.
                </p>
              </CardContent>
            </Card>

            <Card className="retro-frame">
              <CardHeader className="pb-3">
                <CardTitle className="retro-frame-title text-sm">
                  03 · Insight
                </CardTitle>
                <CardDescription>
                  Clear edges, form snapshots and weekly summaries.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Use reports and dashboards to spot value, validate intuition
                  and communicate your reads.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator />

        {/* WEEK INDEX / BROWSER */}
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-2xl font-semibold">Matchup reports</h2>
              <p className="text-sm text-muted-foreground">
                Browse all generated comparison reports by season and week.
              </p>
            </div>
            <Link
              href={`/weeks/${latest.season}/${latest.week}`}
              className="text-sm font-medium underline-offset-4 hover:underline"
            >
              Open latest week →
            </Link>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">
              Available weeks:
            </span>
            {weeks.map((week) => (
              <Link
                key={`${week.season}-${week.week}`}
                href={`/weeks/${week.season}/${week.week}`}
                className="rounded-full border border-border/60 px-3 py-1 text-xs hover:bg-secondary"
              >
                {week.season} · Week {week.week}
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
