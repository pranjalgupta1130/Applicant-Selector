import { useEffect, useState } from "react";

const ESTIMATE = 30; // seconds — typical time for the panel's evaluation

/** Circular countdown shown while the final assessment is being prepared. */
export function ReportCountdown() {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const start = Date.now();
    const t = window.setInterval(() => setElapsed((Date.now() - start) / 1000), 250);
    return () => window.clearInterval(t);
  }, []);
  const left = Math.max(0, Math.ceil(ESTIMATE - elapsed));
  const pct = Math.min(elapsed / ESTIMATE, 0.97);
  const r = 54;
  const c = 2 * Math.PI * r;
  return (
    <div className="flex flex-col items-center gap-4 py-10" role="status" aria-live="polite">
      <div className="relative h-36 w-36">
        <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
          <circle cx="64" cy="64" r={r} fill="none" strokeWidth="8" className="stroke-border" />
          <circle cx="64" cy="64" r={r} fill="none" strokeWidth="8" strokeLinecap="round"
            className="stroke-emerald transition-[stroke-dashoffset] duration-300 ease-linear"
            strokeDasharray={c} strokeDashoffset={c * (1 - pct)} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl tabular-nums text-foreground">{left > 0 ? left : "…"}</span>
          <span className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{left > 0 ? "seconds" : "almost done"}</span>
        </div>
      </div>
      <p className="report-text text-center text-[15px] text-muted-foreground">
        {left > 0 ? "The board is preparing your assessment report." : "Finishing the last details of your report…"}
      </p>
    </div>
  );
}
