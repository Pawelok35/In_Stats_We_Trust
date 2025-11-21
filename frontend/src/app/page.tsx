import Link from "next/link";

const stats = [
  { label: "Weather Scale signals", value: "182", detail: "tracked in current season" },
  { label: "YTD ROI", value: "+34.7%", detail: "after stake sizing & fees" },
  { label: "Confidence hit rate", value: "78%", detail: "across Supercell/Vortex" },
];

const features = [
  {
    title: "Weather Scale intelligence",
    description: "Triple-model agreement with codename staking, built for clarity and speed.",
    icon: "⚡",
  },
  {
    title: "Markdown-to-analytics",
    description: "Automated parsing of matchup reports, turning tables into live charts.",
    icon: "📊",
  },
  {
    title: "Apple-grade UI",
    description: "Glassmorphic cards, gradients, and responsive layout that elevate data.",
    icon: "✨",
  },
  {
    title: "Core12 + PowerScore",
    description: "One deterministic source of truth from raw drives to weekly picks.",
    icon: "🧠",
  },
];

const steps = [
  { title: "Connect data", detail: "Drop markdown reports into data/reports/comparisons." },
  { title: "Generate picks", detail: "Weather Scale codename + stake sizing flows automatically." },
  { title: "Operate & refine", detail: "Use dashboards, insights, and automation hooks." },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#f8fbff] via-white to-[#eef2ff] px-4 pb-20 pt-12 dark:from-[#080a16] dark:via-[#111530] dark:to-[#0b0f1f] sm:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-14">
        <header className="glass-card relative overflow-hidden rounded-[32px] p-8 text-center sm:p-12">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(37,99,235,0.2),transparent_60%)]" />
          <p className="inline-flex items-center justify-center rounded-full border border-white/60 px-4 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-muted-foreground dark:border-white/10 dark:text-white/60">
            In Stats We Trust · Premium NFL analytics
          </p>
          <h1 className="mt-6 text-4xl font-semibold text-slate-900 dark:text-white sm:text-6xl">
            Weather Scale picks meet Apple-grade UX
          </h1>
          <p className="mx-auto mt-4 max-w-3xl text-base text-muted-foreground">
            Run the entire betting intelligence stack—from markdown reports to live dashboards—
            with a single deterministic pipeline. No hype, just polished data infrastructure and
            design.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center rounded-full bg-gradient-to-r from-blue-600 to-teal-400 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/30 transition hover:-translate-y-0.5"
            >
              Launch dashboard
            </Link>
            <Link
              href="https://dribbble.com/search/weather%20scale"
              target="_blank"
              className="inline-flex items-center rounded-full border border-white/60 bg-white/80 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 dark:border-white/15 dark:bg-white/10 dark:text-white/80"
            >
              Design inspiration →
            </Link>
          </div>
          <div className="mt-10 grid gap-4 rounded-[24px] border border-white/60 bg-white/70 p-6 text-left shadow-inner dark:border-white/10 dark:bg-white/5 sm:grid-cols-3">
            {stats.map((stat) => (
              <div key={stat.label}>
                <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{stat.label}</p>
                <p className="text-3xl font-semibold text-slate-900 dark:text-white">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.detail}</p>
              </div>
            ))}
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-4">
          {features.map((feature) => (
            <article key={feature.title} className="glass-card h-full p-5 text-left">
              <div className="text-2xl">{feature.icon}</div>
              <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">{feature.description}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_minmax(0,0.9fr)]">
          <div className="glass-card rounded-[32px] p-8">
            <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Why now</p>
            <h2 className="text-3xl font-semibold text-slate-900 dark:text-white">
              Every matchup, every metric, instantly visualized
            </h2>
            <p className="mt-3 text-sm text-muted-foreground">
              Upload reports, parse them on the server, turn the results into charts, cards, and
              Weather Scale picks. Controlled, explainable analytics that look like a $30k SaaS.
            </p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {["PowerScore flows", "Drive context", "Earnings-ready UI", "Automation hooks"].map(
                (item) => (
                  <div
                    key={item}
                    className="rounded-3xl border border-white/60 bg-white/90 px-4 py-3 text-sm font-medium text-slate-900 dark:border-white/10 dark:bg-white/10 dark:text-white"
                  >
                    {item}
                  </div>
                ),
              )}
            </div>
          </div>
          <div className="glass-card rounded-[32px] bg-gradient-to-br from-blue-600/90 via-indigo-500/80 to-teal-400/80 p-6 text-white shadow-xl">
            <p className="text-xs uppercase tracking-[0.35em]">Next.js + Tailwind + Recharts</p>
            <h3 className="mt-4 text-2xl font-semibold">Engineered for designers & quants</h3>
            <p className="mt-2 text-sm text-white/70">
              We merge deterministic ETL, markdown parsing, and high-end UI primitives to deliver an
              NFL betting copilot you can ship immediately.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-white/80">
              <li>• Responsive Apple/Stripe inspired layout</li>
              <li>• Weather Scale + PowerScore data models</li>
              <li>• Client-side filtering + animated charts</li>
              <li>• Dark/light mode toggle & theming</li>
            </ul>
            <Link
              href="/dashboard"
              className="mt-8 inline-flex items-center justify-center rounded-full bg-white/90 px-5 py-2 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5"
            >
              Explore dashboard →
            </Link>
          </div>
        </section>

        <section className="glass-card rounded-[32px] p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">3-step install</p>
          <h2 className="text-3xl font-semibold text-slate-900 dark:text-white">
            From raw data to premium UI in minutes
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {steps.map((step, idx) => (
              <div
                key={step.title}
                className="rounded-[24px] border border-white/70 bg-white/90 p-5 shadow-inner dark:border-white/10 dark:bg-white/5"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-muted-foreground">
                  {`0${idx + 1}`}
                </p>
                <h4 className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                  {step.title}
                </h4>
                <p className="text-sm text-muted-foreground">{step.detail}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Ready?</p>
          <h2 className="text-3xl font-semibold text-slate-900 dark:text-white">
            Weather Scale insights deserved a premium home.
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Deploy the dashboard, invite your team, and let the data speak with style.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center rounded-full bg-gradient-to-r from-blue-600 to-teal-400 px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5"
            >
              Open dashboard
            </Link>
            <Link
              href="https://github.com/"
              target="_blank"
              className="inline-flex items-center rounded-full border border-white/60 bg-white/80 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 dark:border-white/15 dark:bg-white/10 dark:text-white"
            >
              View repo →
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
