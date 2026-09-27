import { Button } from "@/components/ui/button";
import { downloadReportPdf, type FinalReport } from "@/lib/report";

/** Final assessment report — same content for the candidate and the panel. */
export function FinalReportView({ report }: { report: FinalReport }) {
  return (
    <div className="panel p-6 text-left sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Final assessment report</p>
          <h2 className="mt-1 text-3xl text-foreground">{report.name}</h2>
          <p className="text-[13px] text-muted-foreground">
            {report.roleTitle} · {report.date} · {report.status}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Overall</div>
            <div className="font-display text-4xl tabular-nums text-primary">{report.overallScore ?? "—"}</div>
          </div>
          <Button onClick={() => void downloadReportPdf(report)}>Download PDF</Button>
        </div>
      </div>

      {report.rubric.length > 0 && (
        <div className="mt-6 grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {report.rubric.map((r) => (
            <div key={r.label} className="rounded-lg border border-border bg-secondary/60 p-3">
              <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{r.label}</div>
              <div className="font-display text-2xl text-foreground">{r.score !== null && r.score !== undefined ? r.score : "N/A"}</div>
            </div>
          ))}
        </div>
      )}

      <p className="report-text mt-6 text-[15px] text-foreground">{report.reasoningSummary}</p>

      {(report.covered.length > 0 || report.missing.length > 0) && (
        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          {report.covered.map((c) => (
            <span key={c} className="rounded-md border border-emerald/20 bg-emerald/8 px-3 py-2 text-[12px] leading-5 text-emerald">✓ {c}</span>
          ))}
          {report.missing.map((c) => (
            <span key={c} className="rounded-md border border-warning/20 bg-warning/8 px-3 py-2 text-[12px] leading-5 text-warning">○ {c}</span>
          ))}
        </div>
      )}

      <div className="mt-5 rounded-lg border border-border bg-secondary/60 p-4">
        <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Language notes (not penalised)</p>
        <p className="report-text mt-1 text-[14px] text-foreground">{report.languageSummary || "No non-English usage observed."}</p>
        {report.languageNotes.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {report.languageNotes.map((n, i) => (
              <span key={i} className="rounded-full bg-card px-3 py-1 text-[12px] text-foreground shadow-surface">
                “{n.phrase}” · {n.language}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 space-y-3">
        {report.perQuestion.map((q, i) => (
          <div key={i} className="rounded-lg border border-border p-4">
            <div className="flex justify-between text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
              <span>{q.stage}</span>
              {q.score !== null && <span className="text-primary">{q.score}</span>}
            </div>
            <p className="report-text mt-1 text-[15px] text-foreground">{q.question}</p>
            <p className="report-text mt-2 text-[14px] italic text-muted-foreground">{q.answer}</p>
            {q.note && <p className="mt-2 text-[13px] text-foreground">{q.note}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
