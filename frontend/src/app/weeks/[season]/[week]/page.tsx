import Link from "next/link";
import { notFound } from "next/navigation";

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

type WeekPageParams = {
  season: string;
  week: string;
};

type WeekPageProps = {
  params: Promise<WeekPageParams>;
};

export default async function WeekPage({ params }: WeekPageProps) {
  const { season: seasonParam, week: weekParam } = await params;
  const season = Number(seasonParam);
  const week = Number(weekParam);

  if (!Number.isFinite(season) || !Number.isFinite(week)) {
    notFound();
  }

  const weeks = listAvailableWeeks();
  const current = weeks.find(
    (entry) => entry.season === season && entry.week === week,
  );

  if (!current) {
    notFound();
  }

  const matchups = listMatchupsForWeek(season, week);

  return (
    <main className="min-h-screen bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
        <header className="space-y-4">
          <Link
            href="/"
            className="text-sm font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Powrót do przeglądu
          </Link>
          <div className="space-y-2">
            <Badge variant="outline" className="w-fit text-sm">
              Sezon {season} · Week {week}
            </Badge>
            <h1 className="text-3xl font-semibold sm:text-4xl">
              Raporty match-up
            </h1>
            <p className="text-muted-foreground">
              Wybierz mecz, aby otworzyć szczegółową analizę. Raporty
              renderowane są z plików Markdown generowanych przez pipeline
              In Stats We Trust.
            </p>
          </div>
        </header>

        <Separator />

        <section className="grid gap-4 md:grid-cols-2">
          {matchups.map((matchup) => (
            <Card key={matchup.slug}>
              <CardHeader>
                <CardTitle className="text-xl font-semibold">
                  {matchup.title}
                </CardTitle>
                <CardDescription>
                  {matchup.slug.replace(/_/g, " ").toUpperCase()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link
                  className="text-sm font-medium underline-offset-4 hover:underline"
                  href={`/reports/${season}/${week}/${matchup.slug}`}
                >
                  Otwórz raport →
                </Link>
              </CardContent>
            </Card>
          ))}
          {matchups.length === 0 && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Brak danych</CardTitle>
                <CardDescription>
                  Nie znaleziono raportów match-up dla wybranego tygodnia.
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </section>
      </div>
    </main>
  );
}
