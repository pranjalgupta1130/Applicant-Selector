import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import type { CandidateReport } from "@/lib/interview-data";
import { BoardHeader } from "@/components/BoardHeader";
import { Button } from "@/components/ui/button";
import { CANDIDATE_REPORTS } from "@/lib/interview-data";
import { cn } from "@/lib/utils";
import { downloadReportPdf } from "@/lib/report";

export const Route = createFileRoute("/_authenticated/_admin/panel")({
  head: () => ({
    meta: [
      { title: "Panel review — Boardroom AI" },
      {
        name: "description",
        content:
          "Selection panel view: rubric scores, concept coverage and per-question chalkboard evidence for every DRDO candidate.",
      },
      { property: "og:title", content: "Panel review — Boardroom AI" },
      {
        property: "og:description",
        content: "Rubric breakdown, concept mapping and submitted derivations as evidence.",
      },
    ],
  }),
  component: PanelReview,
});

function PanelReview() {
  const { data: live = [] } = useQuery({ queryKey: ["panel-interviews"], queryFn: loadInterviews, refetchInterval: 15000 });
  const all: PanelEntry[] = [...live, ...CANDIDATE_REPORTS];
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const candidate = all.find((c) => c.id === selectedId) ?? all[0]!;

  return (
    <div className="min-h-screen bg-background">
      <BoardHeader />

      <main className="mx-auto max-w-7xl px-5 pb-20 pt-8 sm:px-8">
        <h1 className="text-3xl text-foreground sm:text-4xl">Panel review</h1>
        <p className="report-text mt-2 max-w-2xl text-[15px] text-muted-foreground">
          Evaluations describe how each candidate reasons — the path taken, the assumptions declared
          and the concepts genuinely engaged with.
        </p>

        <div className="mt-8 grid gap-6 lg:grid-cols-[320px_1fr]">
          {/* Candidate list */}
          <aside className="panel h-fit overflow-hidden">
            <div className="border-b border-border px-4 py-3 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Candidates ({all.length})
            </div>
            <ul>
              {all.map((c) => {
                const active = c.id === selectedId;
                return (
                  <li key={c.id} className="border-b border-border last:border-0">
                    <button
                      type="button"
                      onClick={() => setSelectedId(c.id)}
                      className={cn(
                        "w-full px-4 py-4 text-left transition-colors hover:bg-secondary/70",
                        active && "bg-secondary",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <span className="text-[15px] font-medium text-foreground">{c.name}</span>
                        {c.overallScore !== null ? (
                          <span className="font-display text-xl tabular-nums text-primary">
                            {c.overallScore}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </div>
                      <div className="mt-1 text-[13px] text-muted-foreground">{c.roleTitle}</div>
                      <span
                        className={cn(
                          "mt-2 inline-block rounded-full px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.1em]",
                          c.status === "Completed"
                            ? "bg-emerald/10 text-emerald"
                            : c.status === "Caught cheating"
                              ? "bg-danger/10 text-danger"
                              : "bg-warning/12 text-warning",
                        )}
                      >
                        {c.status}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </aside>

          {/* Detail */}
          <section className="space-y-6">
            <div className="panel p-6 sm:p-8">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl text-foreground">{candidate.name}</h2>
                  <p className="mt-1 text-[13px] text-muted-foreground">
                    {candidate.roleTitle} · Submitted {candidate.submittedAt}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                      Overall
                    </div>
                    <div className="font-display text-4xl tabular-nums text-primary">
                      {candidate.overallScore ?? "—"}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() =>
                      void downloadReportPdf({
                        name: candidate.name,
                        roleTitle: candidate.roleTitle,
                        date: candidate.submittedAt,
                        status: candidate.status,
                        overallScore: candidate.overallScore ?? null,
                        rubric: candidate.rubric.map((r: any) => ({ label: r.label, score: r.score })),
                        covered: candidate.coveredConcepts,
                        missing: candidate.missingConcepts,
                        reasoningSummary: candidate.reasoningSummary,
                        languageSummary: candidate.languageSummary ?? "",
                        languageNotes: candidate.languageNotes ?? [],
                        integrity: (candidate.integrity ?? []) as any[],
                        perQuestion: candidate.perQuestion.map((q: any) => ({
                          stage: q.stage,
                          question: q.question,
                          answer: q.submissionPreview ?? "",
                          score: q.score ?? null,
                          note: q.note ?? "",
                        })),
                      })
                    }
                  >
                    Download PDF report
                  </Button>
                </div>
              </div>

              {candidate.rubric.length > 0 && (
                <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
                  {candidate.rubric.map((r) => (
                    <div key={r.label} className="rounded-xl border border-border bg-secondary/50 p-4">
                      <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                        {r.label}
                      </div>
                      <div className="mt-2 font-display text-2xl tabular-nums text-foreground">
                        {r.score}
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border">
                        <div
                          className="h-full rounded-full bg-emerald"
                          style={{ width: `${r.score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {(candidate.integrity?.length || candidate.languageNotes?.length || candidate.languageSummary) ? (
              <div className="grid gap-6 md:grid-cols-2">
                <div className="panel p-6">
                  <h3 className="text-xl text-foreground">Integrity log</h3>
                  {candidate.integrity?.length ? (
                    <ul className="mt-3 space-y-2">
                      {candidate.integrity.map((e, i) => (
                        <li key={i} className="rounded-lg border border-danger/25 bg-danger/5 px-3 py-2 text-[14px] text-foreground">
                          <span className="font-semibold text-danger">{i === 0 ? "Warning" : "Terminated"}</span> · {e.detail}
                          <span className="block text-[12px] text-muted-foreground">{new Date(e.at).toLocaleTimeString()}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">No violations recorded.</p>
                  )}
                </div>
                <div className="panel p-6">
                  <h3 className="text-xl text-foreground">Language &amp; dialect notes</h3>
                  <p className="mt-1 text-[13px] text-muted-foreground">Noted for context only — never grounds for disqualification.</p>
                  {candidate.languageSummary && <p className="report-text mt-3 text-[15px] text-foreground">{candidate.languageSummary}</p>}
                  <div className="mt-3 grid gap-2">
                    {candidate.languageNotes?.map((n, i) => (
                      <span key={i} className="rounded-full border border-border bg-secondary px-3 py-1 text-[13px] text-foreground" title={n.meaning}>
                        “{n.phrase}” · {n.language}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {/* Concept mapping */}
            <div className="panel p-6 sm:p-8">
              <h3 className="text-xl text-foreground">How they think</h3>
              <p className="mt-1 text-[13px] text-muted-foreground">
                Concept mapping over the reasoning path, not keyword matching.
              </p>
              <div className="mt-6 grid gap-6 sm:grid-cols-2">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.14em] text-emerald">
                    Concepts engaged
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {candidate.coveredConcepts.length ? (
                      candidate.coveredConcepts.map((c) => (
                        <span
                          key={c}
                          className="rounded-md border border-emerald/25 bg-emerald/8 px-3 py-2 text-[12px] leading-5 text-emerald"
                        >
                          {c}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-muted-foreground">Pending completion</span>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] uppercase tracking-[0.14em] text-warning">
                    Concepts not reached
                  </div>
                  <div className="mt-3 grid gap-2">
                    {candidate.missingConcepts.length ? (
                      candidate.missingConcepts.map((c) => (
                        <span
                          key={c}
                          className="rounded-md border border-warning/25 bg-warning/8 px-3 py-2 text-[12px] leading-5 text-warning"
                        >
                          {c}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-muted-foreground">Pending completion</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-6 border-t border-border pt-5">
                <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                  Panel summary
                </div>
                <p className="report-text mt-2 text-[15px] text-foreground">
                  {candidate.reasoningSummary}
                </p>
              </div>
            </div>

            {/* Per-question evidence */}
            <div className="space-y-4">
              <h3 className="text-xl text-foreground">Question-by-question evidence</h3>
              {candidate.perQuestion.length === 0 && (
                <div className="panel p-6 text-sm text-muted-foreground">
                  No submissions yet — this candidate's session is still active.
                </div>
              )}
              {candidate.perQuestion.map((q) => (
                <article key={q.questionId} className="panel p-6">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="rounded-full bg-primary/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-primary">
                      {q.stage}
                    </span>
                    <span className="font-display text-xl tabular-nums text-foreground">
                      {q.score}
                      <span className="text-sm text-muted-foreground">/100</span>
                    </span>
                  </div>
                  <p className="report-text mt-3 text-[17px] text-foreground">{q.question}</p>
                  <div className="mt-4 rounded-lg border border-border bg-secondary/50 p-4">
                    <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                      {q.submissionType} — candidate submission
                    </div>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap font-mono text-[13px] text-foreground">
                      {q.submissionPreview}
                    </pre>
                  </div>
                  <p className="report-text mt-3 text-sm text-muted-foreground">{q.note}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

type PanelEntry = CandidateReport & {
  integrity?: { detail: string; at: string }[];
  languageNotes?: { phrase: string; language: string; meaning: string }[];
  languageSummary?: string;
  status: CandidateReport["status"] | "Caught cheating";
};

async function loadInterviews(): Promise<PanelEntry[]> {
  const { data } = await supabase.from("interviews").select("*").order("created_at", { ascending: false }).limit(100);
  return (data ?? []).map((iv) => {
    const r = (iv.report ?? {}) as Record<string, any>;
    const answers = (iv.answers ?? []) as any[];
    return {
      id: iv.id,
      name: iv.candidate_name ?? "Candidate",
      roleTitle: iv.role_title,
      status: iv.status === "completed" ? "Completed" : iv.status === "disqualified" ? "Caught cheating" : "In Progress",
      overallScore: iv.overall_score,
      submittedAt: new Date(iv.completed_at ?? iv.created_at).toLocaleString(),
      rubric: r["rubric"] ?? [],
      coveredConcepts: r["coveredConcepts"] ?? [],
      missingConcepts: r["missingConcepts"] ?? [],
      reasoningSummary:
        r["reasoningSummary"] ??
        (iv.status === "disqualified" ? "Session terminated after a second integrity violation." : "Session active. Evaluation appears once the interview closes."),
      perQuestion: answers.map((a, i) => {
        const pq = (r["perQuestion"] ?? [])[i] ?? {};
        return {
          questionId: a.itemId ?? String(i),
          stage: a.stage,
          question: a.question,
          submissionType: a.skipped ? "Not attempted" : a.latex ? "Typed equation" : a.hasDrawing ? "Digital chalkboard" : a.spoken ? "Spoken answer (transcribed)" : "Typed answer",
          submissionPreview: a.text || a.latex || (a.hasDrawing ? "[Handwritten derivation]" : "—"),
          score: pq.score ?? 0,
          note: pq.note ?? "",
        } as any;
      }),
      integrity: (iv.integrity_events ?? []) as any,
      languageNotes: answers.flatMap((a) => a.languageNotes ?? []),
      languageSummary: r["languageSummary"],
    };
  });
}
