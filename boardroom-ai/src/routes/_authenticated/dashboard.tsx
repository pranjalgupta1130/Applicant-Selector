import { requireCandidate } from "@/lib/candidate-guard";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { BoardHeader } from "@/components/BoardHeader";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { HELPLINE_EMAIL, NEURO_CONDITIONS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { downloadReportPdf, toFinalReport } from "@/lib/report";
import { FinalReportView } from "@/components/FinalReportView";

export const Route = createFileRoute("/_authenticated/dashboard")({
  ssr: false,
  beforeLoad: ({ context }) => requireCandidate(context.user.id),
  head: () => ({
    meta: [
      { title: "Candidate dashboard — Boardroom AI" },
      { name: "description", content: "Your DRDO interview practice dashboard: begin a session and review your assessment reports." },
      { property: "og:title", content: "Candidate dashboard — Boardroom AI" },
      { property: "og:description", content: "Begin a DRDO interview practice session and review your assessment reports." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Dashboard,
});

type Report = {
  overallScore?: number | null;
  reasoningSummary?: string;
  languageSummary?: string;
};
type Ans = { question: string; languageNotes?: { phrase: string; language: string; meaning: string }[] };

function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data: u } = await supabase.auth.getUser();
      const id = u.user!.id;
      await supabase.rpc("ensure_profile");
      const [{ data: profile }, { data: interviews }] = await Promise.all([
        supabase.from("profiles").select("*").eq("id", id).maybeSingle(),
        supabase.from("interviews").select("*").eq("candidate_id", id).order("created_at", { ascending: false }),
      ]);
      return { profile, interviews: interviews ?? [] };
    },
  });
}

function Dashboard() {
  const { data, isLoading } = useMe();
  const [openId, setOpenId] = useState<string | null>(null);
  const qc = useQueryClient();
  const profile = data?.profile;
  const first = profile?.full_name?.split(" ")[0];

  return (
    <div className="min-h-screen bg-background">
      <BoardHeader />
      <section className="hero-wash">
        <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald">Candidate dashboard</p>
          <h1 className="mt-3 text-4xl text-foreground sm:text-5xl">{first ? `Welcome, ${first}.` : "Welcome."}</h1>
          <p className="report-text mt-3 max-w-2xl text-[15px] text-muted-foreground">
            Sit a full boardroom session, then read how the panel saw your reasoning.
          </p>
          <div className="mt-6">
            <Button asChild size="lg" className="bg-emerald hover:bg-emerald/90">
              <Link to="/apply">Begin a new interview</Link>
            </Button>
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-6xl space-y-12 px-5 pb-20 pt-8 sm:px-8">
        {!isLoading && profile && profile.neurodivergent === null && (
          <NeuroQuestion onDone={() => void qc.invalidateQueries({ queryKey: ["me"] })} />
        )}
        {profile?.neurodivergent && (
          <div className="rounded-xl border border-emerald/30 bg-emerald/8 p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald">Your accessibility setting</p>
            <p className="report-text mt-1 text-[15px] text-foreground">
              We recommend answering derivation questions in the <strong>Equation</strong> section — it opens first for you, with a full symbol
              keyboard so you don't need to write by hand.
            </p>
          </div>
        )}

        {/* Reports */}
        <section>
          <h2 className="text-3xl text-foreground">Your sessions</h2>
          {isLoading && <p className="mt-4 text-sm text-muted-foreground">Loading…</p>}
          {!isLoading && data?.interviews.length === 0 && (
            <div className="panel mt-4 p-6 text-[15px] text-muted-foreground">No sessions yet. Your reports will appear here.</div>
          )}
          <div className="mt-4 space-y-4">
            {data?.interviews.map((iv) => {
              const report = (iv.report ?? {}) as Report;
              const notes = ((iv.answers ?? []) as Ans[]).flatMap((a) => a.languageNotes ?? []);
              return (
                <article key={iv.id} className="panel p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-xl text-foreground">{iv.role_title}</h3>
                      <p className="text-[13px] text-muted-foreground">{new Date(iv.created_at).toLocaleString()}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusPill status={iv.status} />
                      {iv.overall_score !== null && <span className="font-display text-3xl text-primary">{iv.overall_score}</span>}
                    </div>
                  </div>
                  {iv.status === "disqualified" && (
                    <p className="report-text mt-3 text-[14px] text-danger">
                      Closed after repeated integrity violations. To appeal, write to{" "}
                      <a className="underline" href={`mailto:${HELPLINE_EMAIL}`}>{HELPLINE_EMAIL}</a>.
                    </p>
                  )}
                  {report.reasoningSummary && <p className="report-text mt-3 text-[15px] text-foreground">{report.reasoningSummary}</p>}
                  {(notes.length > 0 || report.languageSummary) && (
                    <div className="mt-4 rounded-lg border border-border bg-secondary/60 p-4">
                      <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Language notes (not penalised)</p>
                      {report.languageSummary && <p className="report-text mt-1 text-[14px] text-foreground">{report.languageSummary}</p>}
                      <div className="mt-2 flex flex-wrap gap-2">
                        {notes.map((n, i) => (
                          <span key={i} className="rounded-full bg-card px-3 py-1 text-[12px] text-foreground shadow-surface">
                            “{n.phrase}” · {n.language}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {iv.status !== "in_progress" && (
                    <div className="mt-4 flex flex-wrap gap-3">
                      <Button variant="outline" size="sm" onClick={() => setOpenId(openId === iv.id ? null : iv.id)}>
                        {openId === iv.id ? "Hide full report" : "View full report"}
                      </Button>
                      <Button size="sm" onClick={() => void downloadReportPdf(toFinalReport(iv))}>Download PDF</Button>
                    </div>
                  )}
                  {openId === iv.id && (
                    <div className="mt-5">
                      <FinalReportView report={toFinalReport(iv)} />
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    completed: "bg-emerald/10 text-emerald",
    in_progress: "bg-warning/12 text-warning",
    disqualified: "bg-danger/10 text-danger",
  };
  const label: Record<string, string> = { completed: "Completed", in_progress: "In progress", disqualified: "Caught cheating" };
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.1em]", map[status] ?? "bg-secondary")}>
      {label[status] ?? status}
    </span>
  );
}

function NeuroQuestion({ onDone }: { onDone: () => void }) {
  const [answer, setAnswer] = useState<boolean | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (answer === null) return;
    if (answer && picked.length === 0) {
      toast.error("Select at least one, or choose 'Prefer not to specify'.");
      return;
    }
    setSaving(true);
    const { data: u } = await supabase.auth.getUser();
    await supabase.from("profiles").update({ neurodivergent: answer, conditions: picked }).eq("id", u.user!.id);
    setSaving(false);
    onDone();
  };

  return (
    <section className="panel border-l-4 border-l-primary p-6 sm:p-8">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">One quick question</p>
      <h2 className="mt-2 text-2xl text-foreground">Do you have any neurodivergent condition we should accommodate?</h2>
      <p className="report-text mt-1 text-[14px] text-muted-foreground">
        For example ADHD, dyslexia or autism. This is private and only used to adjust how you answer.
      </p>
      <div className="mt-5 flex gap-3">
        <Button variant={answer === true ? "default" : "outline"} onClick={() => setAnswer(true)}>Yes</Button>
        <Button variant={answer === false ? "default" : "outline"} onClick={() => { setAnswer(false); setPicked([]); }}>No</Button>
      </div>
      {answer && (
        <>
          <div className="mt-5 flex flex-wrap gap-2">
            {[...NEURO_CONDITIONS, "Prefer not to specify"].map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setPicked((p) => (p.includes(c) ? p.filter((x) => x !== c) : [...p, c]))}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-[13px] transition-colors",
                  picked.includes(c) ? "border-emerald bg-emerald/10 text-emerald" : "border-border bg-card text-foreground",
                )}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="mt-5 rounded-lg border border-emerald/30 bg-emerald/8 p-4 text-[14px] text-foreground">
            Thank you. <strong>Please use the Equation section for answering</strong> derivation questions — it has a full keyboard of symbols
            (Greek, trigonometry, calculus, geometry and letters), so you won't need to write by hand.
          </div>
        </>
      )}
      {answer !== null && (
        <Button onClick={() => void save()} disabled={saving} className="mt-5">
          Save
        </Button>
      )}
    </section>
  );
}
