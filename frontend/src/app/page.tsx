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
import {
  listAvailableWeeks,
  listMatchupsForWeek,
} from "@/lib/reports";

export default function Home() {
  const weeks = listAvailableWeeks();

  if (weeks.length === 0) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-background px-6 py-12">
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle>Brak raportów</CardTitle>
            <CardDescription>
              Nie znaleziono wygenerowanych raportów w katalogu
              <code className="ml-1 rounded bg-muted px-1.5 py-0.5 font-mono text-sm">
                data/reports/comparisons
              </code>
              .
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
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
        <header className="space-y-4">
          <Badge variant="outline" className="w-fit text-sm">
            In Stats We Trust · Frontend preview
          </Badge>
          <div>
            <h1 className="text-3xl font-semibold sm:text-4xl">
              Raporty porównawcze
            </h1>
            <p className="mt-2 text-muted-foreground">
              Przeglądaj wygenerowane raporty match-up wprost z katalogu
              danych. Wybierz tydzień i otwórz analizę konkretnego meczu.
            </p>
          </div>
        </header>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">
              Dostępne tygodnie:
            </span>
            {weeks.map((week) => (
              <Link
                key={`${week.season}-${week.week}`}
                href={`/weeks/${week.season}/${week.week}`}
                className="text-sm underline-offset-4 hover:underline"
              >
                {week.season} · Week {week.week}
              </Link>
            ))}
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold">
                Ostatni tydzień: {latest.season}, Week {latest.week}
              </h2>
              <p className="text-muted-foreground">
                {matchups.length} dostępnych raportów match-up.
              </p>
            </div>
            <Link
              className="text-sm font-medium underline-offset-4 hover:underline"
              href={`/weeks/${latest.season}/${latest.week}`}
            >
              Zobacz wszystkie →
            </Link>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {matchups.map((matchup) => (
              <Card key={matchup.slug}>
                <CardHeader>
                  <CardTitle className="text-xl font-semibold">
                    {matchup.title}
                  </CardTitle>
                  <CardDescription>
                    Raport porównawczy sezon {latest.season}, week{" "}
                    {latest.week}.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Link
                    href={`/reports/${latest.season}/${latest.week}/${matchup.slug}`}
                    className="text-sm font-medium underline-offset-4 hover:underline"
                  >
                    Otwórz raport →
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
