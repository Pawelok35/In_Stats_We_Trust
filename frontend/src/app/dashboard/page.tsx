import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { parseMatchupReport } from "@/lib/markdown-parser";
import {
  listAvailableWeeks,
  listMatchupsForWeek,
  loadMatchupMarkdown,
  type MatchupSummary,
  type WeekIdentifier,
} from "@/lib/reports";

export default function DashboardPage() {
  const weeks = listAvailableWeeks();
  const initialWeek = weeks[0];

  if (!initialWeek) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-6 py-12">
        <div className="glass-card max-w-lg space-y-3 p-8 text-center text-sm text-muted-foreground">
          <h1 className="text-2xl font-semibold text-foreground">No matchup reports available</h1>
          <p>
            Generate markdown reports inside{" "}
            <code className="rounded-lg bg-secondary px-2 py-1 text-xs">data/reports/comparisons</code>{" "}
            to activate the dashboard.
          </p>
        </div>
      </main>
    );
  }

  const { matchups, parsedReport } = loadInitialReport(initialWeek);

  return (
    <DashboardShell
      initialWeeks={weeks}
      initialWeek={initialWeek}
      initialMatchups={matchups}
      initialReport={parsedReport}
    />
  );
}

function loadInitialReport(initialWeek: WeekIdentifier) {
  const matchups: MatchupSummary[] = listMatchupsForWeek(initialWeek.season, initialWeek.week);
  const firstSlug = matchups[0]?.slug;
  const parsedReport =
    firstSlug !== undefined
      ? parseMatchupReport(
          firstSlug,
          loadMatchupMarkdown(initialWeek.season, initialWeek.week, firstSlug),
        )
      : null;

  return { matchups, parsedReport };
}
