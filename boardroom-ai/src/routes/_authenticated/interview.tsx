import { requireCandidate } from "@/lib/candidate-guard";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { BoardHeader } from "@/components/BoardHeader";
import { Chalkboard, type ChalkboardHandle } from "@/components/Chalkboard";
import { ReasoningAnswer, type ReasoningHandle } from "@/components/ReasoningAnswer";
import { QuestionTimer } from "@/components/QuestionTimer";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { getLocalUser } from "@/lib/local-auth";
import { useProctor, type Violation } from "@/hooks/useProctor";
import type { FinalReport, LanguageNote } from "@/lib/report";
import { FinalReportView } from "@/components/FinalReportView";
import { ReportCountdown } from "@/components/ReportCountdown";
import {
  DEFAULT_SETTINGS,
  ROLES,
  type CandidateProfile,
} from "@/lib/interview-data";
import { createInterview, getInterviewReport, recordInterviewIntegrity, startInterview, submitInterviewAnswer, type BackendQuestion } from "@/lib/backend-api";
import { HELPLINE_EMAIL } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { QuestionReadAloud } from "@/components/QuestionReadAloud";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/interview")({
  ssr: false,
  beforeLoad: () => requireCandidate(),
  head: () => ({
    meta: [
      { title: "Interview in session — Boardroom AI" },
      { name: "description", content: "A timed, proctored DRDO panel interview with smart follow-up questions." },
      { property: "og:title", content: "Interview in session — Boardroom AI" },
      { property: "og:description", content: "Single-pass questions, follow-ups, chalkboard, typing and voice answers." },
    ],
  }),
  component: InterviewScreen,
});

const { timerSeconds, warningThresholdSeconds } = DEFAULT_SETTINGS;

type Item = {
  id: string;
  text: string;
  stage: string;
  kind: "derivation" | "reasoning";
  mainIndex: number;
  isFollowUp: boolean;
};

type Answer = {
  itemId: string;
  question: string;
  stage: string;
  isFollowUp: boolean;
  kind: string;
  text?: string | undefined;
  latex?: string | undefined;
  hasDrawing: boolean;
  spoken: boolean;
  secondsUsed: number;
  skipped: boolean;
  languageNotes: LanguageNote[];
  score?: number | undefined;
  evaluationNote?: string | undefined;
};

type Phase = "gate" | "live" | "thinking" | "transition" | "done" | "disqualified";

function InterviewScreen() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [neuro, setNeuro] = useState(false);
  const [name, setName] = useState<string>("");
  const [phase, setPhase] = useState<Phase>("gate");
  const [transitionMsg, setTransitionMsg] = useState("");
  const [item, setItem] = useState<Item | null>(null);
  const [warned, setWarned] = useState(false);
  const [confirmEmpty, setConfirmEmpty] = useState(false);
  const [warning, setWarning] = useState<Violation | null>(null);
  const [lastViolation, setLastViolation] = useState<Violation | null>(null);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);

  const interviewId = useRef<string | null>(null);
  const board = useRef<ChalkboardHandle | null>(null);
  const reasoning = useRef<ReasoningHandle | null>(null);
  const answers = useRef<Answer[]>([]);
  const events = useRef<Violation[]>([]);
  const strikes = useRef(0);
  const remaining = useRef(timerSeconds);
  const candidateName = useRef("Candidate");

  useEffect(() => {
    const raw = sessionStorage.getItem("boardroom.profile");
    if (!raw) {
      navigate({ to: "/apply", replace: true });
      return;
    }
    setProfile(JSON.parse(raw) as CandidateProfile);
    const user = getLocalUser();
    if (user) {
      let neuroSetting = false;
      try {
        const stored = localStorage.getItem(`boardroom.neuro.${user.id}`);
        if (stored) {
          const parsed = JSON.parse(stored);
          neuroSetting = Boolean(parsed.neurodivergent);
        }
      } catch {}
      setNeuro(neuroSetting);
      const displayName = user.name ?? user.email ?? "Candidate";
      setName(displayName);
      candidateName.current = displayName;
    }
  }, [navigate]);

  const role = ROLES.find((r) => r.id === profile?.roleId) ?? ROLES[0]!;

  const persist = useCallback(async (extra: Record<string, unknown> = {}) => {
    if (!interviewId.current) return;
    await recordInterviewIntegrity(interviewId.current, events.current, typeof extra.status === "string" ? extra.status : undefined).catch((error) => {
      console.error("Could not persist interview integrity events", error);
    });
  }, []);

  /* ---------- Proctoring: one warning, then the test closes ---------- */
  const proctor = useProctor({
    active: phase === "live" || phase === "thinking" || phase === "transition",
    onViolation: (v) => {
      events.current = [...events.current, v];
      strikes.current += 1;
      setLastViolation(v);
      if (strikes.current >= 2) {
        setPhase("disqualified");
        setWarning(null);
        proctor.stopAll();
        void persist({ status: "disqualified", completed_at: new Date().toISOString() });
      } else {
        setWarning(v);
        void persist();
      }
    },
  });

  const asItem = (q: BackendQuestion): Item => ({
    id: q._id || q.id, text: q.text, stage: q.stage.replaceAll("_", " "),
    kind: q.questionType === "implementation" || q.questionType === "design" ? "derivation" : "reasoning",
    mainIndex: answers.current.length, isFollowUp: q.questionType === "follow_up",
  });

  const start = async () => {
    const ok = proctor.camReady || (await proctor.startCamera());
    if (!ok) return;
    // Ask for the microphone now so no permission pop-up interrupts the session later.
    await navigator.mediaDevices.getUserMedia({ audio: true }).then((s) => s.getTracks().forEach((t) => t.stop())).catch(() => undefined);
    await document.documentElement.requestFullscreen?.().catch(() => undefined);
    const user = getLocalUser();
    if (!user) return;
    try {
      if (!profile?.backendCandidateId || !profile.backendRoleId) throw new Error("Candidate or advertised post is missing from the backend profile. Return to application setup.");
      const created = await createInterview(profile.backendCandidateId, profile.backendRoleId);
      interviewId.current = created._id;
      const started = await startInterview(created._id);
      if (!started.question) throw new Error("The interview service did not return an opening question.");
      setItem(asItem(started.question));
      remaining.current = timerSeconds;
      setPhase("live");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not start the interview.");
    }
  };

  const goNext = (next: Item | null, msg: string) => {
    setTransitionMsg(msg);
    setPhase("transition");
    window.setTimeout(async () => {
      setWarned(false);
      remaining.current = timerSeconds;
      if (!next) {
        setPhase("done");
        proctor.stopAll();
        await persist();
        if (interviewId.current) {
          try {
            console.info(`[REPORT TRACE] location=browser requesting final report interviewId=${interviewId.current}`);
            const report = await getInterviewReport(interviewId.current);
            const scorecard = (report.scorecard || {}) as Record<string, any>;
            const competencies = (report.competencyScores || scorecard.competencies || []) as Array<{ competency: string; score: number | null; status?: string }>;
            const rubric = competencies.map((c) => ({
              label: c.competency,
              score: c.score !== null && c.score !== undefined ? c.score : "N/A (untested)"
            }));
            const overall = Number(report.overallScore ?? scorecard.overallScore ?? scorecard.scorecard?.overallScore ?? 0);
            const covered = (report.strengths && report.strengths.length > 0 ? report.strengths : (scorecard.strengths || [])).map((s: any) => typeof s === "string" ? s : s.area || s.evidence || String(s));
            const missing = (report.gaps && report.gaps.length > 0 ? report.gaps : (scorecard.gaps || [])).map((s: any) => typeof s === "string" ? s : s.area || s.evidence || String(s));
            const reasoningSummary = scorecard.explanation || scorecard.decisionSupport?.recommendationNote || report.recommendations?.[0] || "Evidence-based assessment generated by the interview service.";

            console.info("[REPORT TRACE] location=frontend immediately before rendering FinalReportView", JSON.stringify({
              interviewId: interviewId.current,
              overallScore: overall,
              rubric,
              coveredCount: covered.length,
              missingCount: missing.length
            }));

            const finalRep: FinalReport = {
              name: candidateName.current,
              roleTitle: role.title,
              date: new Date().toLocaleString(),
              status: "Completed",
              overallScore: overall,
              rubric,
              covered,
              missing,
              reasoningSummary,
              languageSummary: "Language use is not part of the technical score.",
              languageNotes: [],
              integrity: events.current,
              perQuestion: answers.current.map((a) => ({
                stage: a.stage,
                question: a.question,
                answer: a.text || a.latex || "(not attempted)",
                score: a.score ?? null,
                note: a.evaluationNote || "See competency scorecard."
              })),
            };

            setFinalReport(finalRep);

            const sessionReportItem = {
              id: interviewId.current,
              role_title: role.title,
              created_at: new Date().toISOString(),
              status: "completed",
              overall_score: overall,
              report: finalRep,
              answers: answers.current,
            };
            const currentUser = getLocalUser();
            if (currentUser) {
              try {
                const raw = localStorage.getItem(`boardroom.interviews.${currentUser.id}`);
                const existing = raw ? JSON.parse(raw) : [];
                localStorage.setItem(`boardroom.interviews.${currentUser.id}`, JSON.stringify([sessionReportItem, ...existing]));
              } catch {}
            }
          } catch (error) { toast.error(error instanceof Error ? error.message : "The scorecard could not be loaded."); }
        }
        return;
      }
      setItem(next);
      setPhase("live");
    }, 1400);
  };

  const commit = async (reason: "time-up" | "submitted", forceEmpty = false) => {
    if (!item) return;
    let answerText = "";
    let rec: Answer;
    const base = {
      itemId: item.id,
      question: item.text,
      stage: item.stage,
      isFollowUp: item.isFollowUp,
      kind: item.kind,
      secondsUsed: timerSeconds - remaining.current,
      languageNotes: [] as LanguageNote[],
    };
    if (item.kind === "reasoning") {
      const r = reasoning.current?.get();
      answerText = r?.text ?? "";
      rec = { ...base, text: answerText, hasDrawing: false, spoken: Boolean(r?.spoken), skipped: forceEmpty || !answerText };
    } else {
      const s = board.current?.getSubmission();
      answerText = s?.latex ?? (s?.canvasDataUrl ? "[handwritten derivation on chalkboard]" : "");
      rec = { ...base, latex: s?.latex, hasDrawing: Boolean(s?.canvasDataUrl), spoken: false, skipped: forceEmpty || Boolean(s?.empty) };
    }
    answers.current = [...answers.current, rec];
    void persist();

    setPhase("thinking");
    if (phaseRef.current === "disqualified") return;

    const lead = reason === "time-up" ? "Time's up" : "Response recorded";
    try {
      const result = await submitInterviewAnswer(interviewId.current!, item.id, answerText || "(not attempted)");
      rec.score = Number(result.evaluation.score ?? 0);
      rec.evaluationNote = typeof result.evaluation.reasoning === "string" ? result.evaluation.reasoning : "Answer assessed by the Python evaluator.";
      void persist();
      const verdict = rec.evaluationNote;
      if (typeof verdict === "string") toast.message(verdict.slice(0, 180));
      goNext(result.nextQuestion ? asItem(result.nextQuestion) : null, result.nextQuestion ? `${lead} — the panel has adapted its next question` : `${lead} — the assessment is complete`);
    } catch (error) {
      setPhase("live");
      toast.error(error instanceof Error ? error.message : "Could not submit your answer.");
    }
  };

  const phaseRef = useRef(phase);
  phaseRef.current = phase;

  const onExpire = useCallback(() => {
    if (phaseRef.current === "live") void commit("time-up");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item]);

  const onTick = useCallback((r: number) => {
    remaining.current = r;
    if (r === warningThresholdSeconds) setWarned(true);
  }, []);

  const handleSubmit = () => {
    const empty = item?.kind === "reasoning" ? reasoning.current?.get().empty : board.current?.getSubmission().empty;
    if (empty) return setConfirmEmpty(true);
    void commit("submitted");
  };

  const flag = (type: string, detail: string) => proctor.fire(type, detail);

  /* ---------- Screens ---------- */

  if (phase === "disqualified") {
    return (
      <div className="min-h-screen bg-background">
        <BoardHeader showNav={false} />
        <main className="mx-auto max-w-2xl px-5 py-20 text-center sm:px-8">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-danger">Session terminated</p>
          <h1 className="mt-3 text-4xl text-foreground">This interview has been closed for a second integrity violation.</h1>
          <p className="report-text mt-4 text-[15px] text-muted-foreground">
            After one warning, a further violation was detected
            {lastViolation ? <> — <strong className="text-foreground">{lastViolation.detail.toLowerCase()}</strong></> : null}. Under the
            examination conditions you accepted, the candidate has been recorded as caught cheating and the panel has been notified.
          </p>
          <div className="mt-8 rounded-xl border border-border bg-card p-5 text-left shadow-surface">
            <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">Believe this is a mistake?</p>
            <p className="report-text mt-2 text-[15px] text-foreground">
              You may approach the DRDO recruitment cell to appeal. Write to{" "}
              <a className="font-semibold text-primary underline" href={`mailto:${HELPLINE_EMAIL}`}>{HELPLINE_EMAIL}</a> with your name and the
              time of your session.
            </p>
          </div>
          <Button asChild variant="outline" className="mt-8">
            <Link to="/dashboard">Return to dashboard</Link>
          </Button>
        </main>
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="min-h-screen bg-background">
        <BoardHeader showNav={false} />
        <main className="mx-auto max-w-4xl px-5 py-14 sm:px-8">
          <div className="text-center">
            <p className="text-[11px] uppercase tracking-[0.2em] text-emerald">Session closed</p>
            <h1 className="mt-3 text-4xl text-foreground">Thank you. Here is your assessment.</h1>
          </div>
          <div className="mt-8">
            {finalReport ? (
              <FinalReportView report={finalReport} />
            ) : (
              <ReportCountdown />
            )}
          </div>
          <div className="mt-8 text-center">
            <Button asChild variant="outline">
              <Link to="/dashboard">Go to my dashboard</Link>
            </Button>
          </div>
        </main>
      </div>
    );
  }

  const camBox = (
    <div className="panel overflow-hidden">
      <div className="relative aspect-[4/3] bg-primary/90">
        <video ref={proctor.videoRef} muted playsInline className="h-full w-full -scale-x-100 object-cover" />
        {!proctor.camReady && (
          <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-[13px] text-primary-foreground/80">
            Camera preview
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 px-3 py-2 text-[12px]">
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            proctor.status === "ok" ? "bg-emerald" : "bg-warning",
            !proctor.camReady && "bg-muted-foreground",
          )}
        />
        <span className="text-muted-foreground">
          {!proctor.camReady
            ? "Camera off"
            : !proctor.trackerReady && phase !== "gate"
              ? "Starting gaze tracking…"
              : proctor.status === "ok"
                ? "Eyes on screen"
                : proctor.status === "noface"
                  ? "Face not visible"
                  : proctor.status === "multi"
                    ? "More than one person"
                    : "Looking away"}
        </span>
      </div>
    </div>
  );

  if (phase === "gate") {
    return (
      <div className="min-h-screen bg-background">
        <BoardHeader showNav={false} />
        <main className="hero-wash mx-auto grid max-w-5xl gap-8 px-5 py-12 sm:px-8 md:grid-cols-[1fr_320px]">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald">Secure session</p>
            <h1 className="mt-3 text-4xl text-foreground">Before the panel calls you in</h1>
            <ul className="report-text mt-5 space-y-2 text-[15px] text-foreground">
              <li>• Your camera stays on. Keep your face centred and your eyes on this screen.</li>
              <li>• The interview runs in full screen. Leaving it, switching tabs or opening other apps is detected.</li>
              <li>• Copy, paste, screenshots, second monitors, AI overlays and teleprompters are not permitted.</li>
              <li>• <strong>You get one warning.</strong> A second violation closes the test and records you as caught cheating.</li>
            </ul>
            {neuro && (
              <div className="mt-5 rounded-lg border border-emerald/30 bg-emerald/8 p-4 text-[14px] text-foreground">
                You told us you are neurodivergent. For derivation questions the <strong>Equation</strong> section opens first — we recommend
                answering there.
              </div>
            )}
            {proctor.camError && <p className="mt-4 text-[14px] text-danger">{proctor.camError}</p>}
            <div className="mt-8 flex flex-wrap gap-3">
              {!proctor.camReady && (
                <Button variant="outline" onClick={() => void proctor.startCamera()}>
                  Turn on camera
                </Button>
              )}
              <Button onClick={() => void start()} className="bg-emerald hover:bg-emerald/90">
                Enter the boardroom
              </Button>
            </div>
          </div>
          <div>{camBox}</div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen select-none bg-background">
      <BoardHeader
        showNav={false}
        right={
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-[12px] text-muted-foreground sm:flex">
              <span className="h-2 w-2 rounded-full bg-emerald" />
              Session active · proctored
            </span>
            {item && (
              <QuestionTimer
                questionKey={item.id}
                seconds={timerSeconds}
                warningAt={warningThresholdSeconds}
                paused={phase !== "live"}
                onExpire={onExpire}
                onTick={onTick}
              />
            )}
          </div>
        }
      />

      <main className="mx-auto grid max-w-6xl gap-6 px-5 pb-20 pt-8 sm:px-8 lg:grid-cols-[1fr_240px]">
        <div>
          {(phase === "transition" || phase === "thinking") && (
            <div className="rounded-xl border border-border bg-card p-6 text-center shadow-surface">
              <p className="font-display text-2xl text-primary">
                {phase === "thinking" ? "The panel is considering your answer…" : transitionMsg}
              </p>
              <p className="mt-1 text-[13px] text-muted-foreground">This question is now closed and cannot be revisited.</p>
            </div>
          )}

          {item && phase === "live" && (
            <>
              <article className={cn("panel p-6 sm:p-8", item.isFollowUp && "border-l-4 border-l-emerald")}>
                <span
                  className={cn(
                    "inline-block rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
                    item.isFollowUp ? "bg-emerald/10 text-emerald" : "bg-primary/8 text-primary",
                  )}
                >
                  {item.stage}
                </span>
                <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <p className="report-text min-w-0 max-w-3xl text-[20px] leading-relaxed text-foreground sm:text-[22px]">{item.text}</p>
                  <QuestionReadAloud question={item.text} questionKey={item.id} />
                </div>
              </article>

              {warned && (
                <div className="mt-4 rounded-lg border border-warning/40 bg-warning/8 px-4 py-3 text-[14px] text-foreground">
                  <strong className="font-semibold text-warning">20 seconds left</strong> — this question will close and cannot be revisited
                  once time expires.
                </div>
              )}

              <div className="mt-6">
                {item.kind === "reasoning" ? (
                  <ReasoningAnswer
                    ref={reasoning}
                    questionKey={item.id}
                    onPasteBlocked={() => flag("clipboard", "Tried to paste text into the answer")}
                    onTypingBurst={() => flag("text_injection", "A large block of text appeared at once (possible AI-generated insertion)")}
                  />
                ) : (
                  <>
                    {neuro && (
                      <p className="mb-3 rounded-lg bg-emerald/8 px-4 py-2 text-[13px] text-emerald">
                        Recommended for you: answer in the Equation section.
                      </p>
                    )}
                    <Chalkboard ref={board} questionKey={item.id} preferEquation={neuro} />
                  </>
                )}
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <Button onClick={handleSubmit} className="bg-emerald hover:bg-emerald/90">
                  Submit answer
                </Button>
                <p className="text-[13px] text-muted-foreground">Submitting closes this question permanently.</p>
              </div>
            </>
          )}
        </div>
        <aside className="order-first lg:order-none">
          <div className="lg:sticky lg:top-28">{camBox}</div>
        </aside>
      </main>

      <AlertDialog open={confirmEmpty} onOpenChange={setConfirmEmpty}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-display text-2xl">Submit an empty answer?</AlertDialogTitle>
            <AlertDialogDescription className="report-text">
              Nothing has been written, typed or spoken. If you submit now, this question will be recorded as not attempted and cannot be
              revisited.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep working</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setConfirmEmpty(false);
                void commit("submitted", true);
              }}
            >
              Submit empty
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={Boolean(warning)}>
        <AlertDialogContent className="border-danger/40">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-display text-2xl text-danger">Integrity warning — final chance</AlertDialogTitle>
            <AlertDialogDescription className="report-text text-foreground">
              We detected: <strong>{warning?.detail}</strong>. This has been recorded for the panel. Any further violation will close the test
              immediately and mark you as caught cheating.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction
              onClick={() => {
                setWarning(null);
                if (!document.fullscreenElement) void document.documentElement.requestFullscreen?.().catch(() => undefined);
              }}
            >
              I understand — continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
