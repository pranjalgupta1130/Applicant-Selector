import { requireCandidate } from "@/lib/candidate-guard";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { supabase } from "@/integrations/supabase/client";
import { useProctor, type Violation } from "@/hooks/useProctor";
import { followUp, finalizeInterview, type LanguageNote } from "@/lib/interview.functions";
import { toFinalReport, type FinalReport } from "@/lib/report";
import { FinalReportView } from "@/components/FinalReportView";
import { ReportCountdown } from "@/components/ReportCountdown";
import {
  DEFAULT_SETTINGS,
  ROLES,
  buildQuestionSet,
  questionKind,
  type CandidateProfile,
} from "@/lib/interview-data";
import { HELPLINE_EMAIL } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { QuestionReadAloud } from "@/components/QuestionReadAloud";

export const Route = createFileRoute("/_authenticated/interview")({
  ssr: false,
  beforeLoad: ({ context }) => requireCandidate(context.user.id),
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

const { timerSeconds, warningThresholdSeconds, questionsPerInterview } = DEFAULT_SETTINGS;

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
};

type Phase = "gate" | "live" | "thinking" | "transition" | "done" | "disqualified";

function InterviewScreen() {
  const navigate = useNavigate();
  const askFollowUp = useServerFn(followUp);
  const finalize = useServerFn(finalizeInterview);

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
  const mainIdx = useRef(0);
  const followCount = useRef(0);
  const followTarget = useRef(1);
  const followHistory = useRef<string[]>([]);

  useEffect(() => {
    const raw = sessionStorage.getItem("boardroom.profile");
    if (!raw) {
      navigate({ to: "/apply", replace: true });
      return;
    }
    setProfile(JSON.parse(raw) as CandidateProfile);
    void supabase.auth.getUser().then(async ({ data }) => {
      if (!data.user) return;
      const { data: p } = await supabase.from("profiles").select("full_name, neurodivergent").eq("id", data.user.id).maybeSingle();
      setNeuro(Boolean(p?.neurodivergent));
      setName(p?.full_name ?? data.user.email ?? "Candidate");
    });
  }, [navigate]);

  const role = ROLES.find((r) => r.id === profile?.roleId) ?? ROLES[0]!;
  const mains = useMemo(() => buildQuestionSet(role.id, questionsPerInterview), [role.id]);

  const persist = useCallback(async (extra: Record<string, unknown> = {}) => {
    if (!interviewId.current) return;
    await supabase
      .from("interviews")
      .update({ answers: answers.current as never, integrity_events: events.current as never, warnings: strikes.current, ...extra })
      .eq("id", interviewId.current);
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

  const mainItem = (i: number): Item | null => {
    const q = mains[i];
    if (!q) return null;
    return { id: q.id, text: q.text, stage: q.stage, kind: questionKind(q), mainIndex: i, isFollowUp: false };
  };

  const beginMain = (i: number) => {
    mainIdx.current = i;
    followCount.current = 0;
    followHistory.current = [];
    const q = mains[i];
    // Only the second (core role) question gets follow-ups — exactly two.
    followTarget.current = i === 1 ? 2 : 0;
    return mainItem(i);
  };

  const start = async () => {
    const ok = proctor.camReady || (await proctor.startCamera());
    if (!ok) return;
    // Ask for the microphone now so no permission pop-up interrupts the session later.
    await navigator.mediaDevices.getUserMedia({ audio: true }).then((s) => s.getTracks().forEach((t) => t.stop())).catch(() => undefined);
    await document.documentElement.requestFullscreen?.().catch(() => undefined);
    const { data: u } = await supabase.auth.getUser();
    if (!u.user) return;
    const { data } = await supabase
      .from("interviews")
      .insert({ candidate_id: u.user.id, candidate_name: name, role_id: role.id, role_title: role.title })
      .select("id")
      .single();
    interviewId.current = data?.id ?? null;
    setItem(beginMain(0));
    remaining.current = timerSeconds;
    setPhase("live");
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
          await finalize({ data: { interviewId: interviewId.current } }).catch(() => undefined);
          const { data: row } = await supabase.from("interviews").select("*").eq("id", interviewId.current).single();
          if (row) setFinalReport(toFinalReport(row));
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

    const wantFollowUp = followCount.current < followTarget.current;
    setPhase("thinking");
    const res = await askFollowUp({
      data: {
        roleTitle: role.title,
        question: item.text,
        answer: answerText.slice(0, 8000),
        history: followHistory.current.slice(-6),
        wantFollowUp,
        spoken: rec.spoken,
      },
    }).catch(() => null);
    if (res?.languageNotes?.length) {
      rec.languageNotes = res.languageNotes;
      void persist();
    }
    if (phaseRef.current === "disqualified") return;

    const lead = reason === "time-up" ? "Time's up" : "Response recorded";
    if (wantFollowUp && res?.followUp) {
      followCount.current += 1;
      followHistory.current.push(res.followUp);
      goNext(
        {
          id: `${mains[mainIdx.current]?.id}-f${followCount.current}`,
          text: res.followUp,
          stage: "Follow-up",
          kind: res.kind === "derivation" ? "derivation" : "reasoning",
          mainIndex: mainIdx.current,
          isFollowUp: true,
        },
        `${lead} — the panel has a follow-up`,
      );
    } else {
      goNext(beginMain(mainIdx.current + 1), `${lead} — moving to next question`);
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
