import { requireCandidate } from "@/lib/candidate-guard";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { BoardHeader } from "@/components/BoardHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ROLES, DEFAULT_SETTINGS, type CandidateProfile } from "@/lib/interview-data";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/apply")({
  ssr: false,
  beforeLoad: ({ context }) => requireCandidate(context.user.id),
  head: () => ({
    meta: [
      { title: "Begin your interview — Boardroom AI" },
      {
        name: "description",
        content:
          "Select the DRDO role you applied for, share your profile, and enter a timed boardroom panel interview with a digital chalkboard.",
      },
      { property: "og:title", content: "Begin your interview — Boardroom AI" },
      {
        property: "og:description",
        content: "Role selection, profile and interview format for a DRDO panel simulation.",
      },
    ],
  }),
  component: Onboarding,
});

const STEPS = ["Role", "Profile", "Confirmation"];

function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [roleId, setRoleId] = useState<string | null>(null);
  const [resumeName, setResumeName] = useState<string | null>(null);
  const [years, setYears] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [skillDraft, setSkillDraft] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);

  const role = ROLES.find((r) => r.id === roleId) ?? null;

  const addSkill = () => {
    const value = skillDraft.trim().replace(/,$/, "");
    if (!value) return;
    if (skills.some((s) => s.toLowerCase() === value.toLowerCase())) {
      setSkillDraft("");
      return;
    }
    setSkills((prev) => [...prev, value]);
    setSkillDraft("");
  };

  const next = () => {
    if (step === 0 && !roleId) {
      toast.error("Select the role you are applying for to continue.");
      return;
    }
    if (step === 1) {
      if (!resumeName) {
        toast.error("Upload your resume to continue.");
        return;
      }
      const y = Number(years);
      if (years.trim() === "" || Number.isNaN(y) || y < 0 || y > 50) {
        toast.error("Enter your years of experience (0–50).");
        return;
      }
      if (skills.length === 0) {
        toast.error("Add at least one key skill.");
        return;
      }
    }
    setStep((s) => Math.min(STEPS.length - 1, s + 1));
  };

  const startInterview = () => {
    if (!role) return;
    const profile: CandidateProfile = {
      roleId: role.id,
      resumeName,
      yearsExperience: years,
      skills,
    };
    sessionStorage.setItem("boardroom.profile", JSON.stringify(profile));
    navigate({ to: "/interview" });
  };

  return (
    <div className="min-h-screen bg-background">
      <BoardHeader />

      <main className="mx-auto max-w-5xl px-5 pb-20 pt-10 sm:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-emerald">
          Selector–Applicant Simulation
        </p>
        <h1 className="mt-3 text-4xl leading-tight text-foreground sm:text-5xl">
          Take your seat at the table.
        </h1>
        <p className="report-text mt-4 max-w-2xl text-[15px] text-muted-foreground">
          This session mirrors the DRDO boardroom format: questions are put to you one at a time, you
          derive on a digital chalkboard, and the panel reviews how you think — not which keywords
          you recall.
        </p>

        {/* Step rail */}
        <div className="mt-10 flex items-center gap-3">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-3">
              <div
                className={cn(
                  "flex items-center gap-2 rounded-full border px-3 py-1.5 text-[13px]",
                  i === step
                    ? "border-primary bg-primary text-primary-foreground"
                    : i < step
                      ? "border-emerald/40 bg-emerald/10 text-emerald"
                      : "border-border bg-card text-muted-foreground",
                )}
              >
                <span className="tabular-nums">{i + 1}</span>
                {label}
              </div>
              {i < STEPS.length - 1 && <span className="h-px w-8 bg-border sm:w-14" />}
            </div>
          ))}
        </div>

        <section className="mt-8">
          {step === 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {ROLES.map((r) => {
                const selected = roleId === r.id;
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setRoleId(r.id)}
                    aria-pressed={selected}
                    className={cn(
                      "panel p-5 text-left transition-all hover:shadow-raised",
                      selected && "border-emerald ring-1 ring-emerald/40",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h2 className="text-xl text-foreground">{r.title}</h2>
                      <span className="shrink-0 rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.1em] text-muted-foreground">
                        {r.openings} openings
                      </span>
                    </div>
                    <p className="mt-1 text-[13px] font-medium text-emerald">{r.department}</p>
                    <p className="report-text mt-2 text-sm text-muted-foreground">{r.summary}</p>
                  </button>
                );
              })}
            </div>
          )}

          {step === 1 && (
            <div className="panel p-6 sm:p-8">
              <h2 className="text-2xl text-foreground">Your profile</h2>
              <div className="mt-6 space-y-6">
                <div>
                  <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                    Resume
                  </Label>
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragging(true);
                    }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setDragging(false);
                      const file = e.dataTransfer.files?.[0];
                      if (file) setResumeName(file.name);
                    }}
                    onClick={() => fileInput.current?.click()}
                    className={cn(
                      "mt-2 cursor-pointer rounded-xl border border-dashed p-8 text-center transition-colors",
                      dragging ? "border-emerald bg-emerald/5" : "border-input bg-secondary/50",
                    )}
                  >
                    <p className="text-sm font-medium text-foreground">
                      {resumeName ?? "Drag and drop your resume here"}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {resumeName ? "Click to replace" : "PDF or DOCX, up to 5 MB"}
                    </p>
                    <input
                      ref={fileInput}
                      type="file"
                      accept=".pdf,.doc,.docx"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setResumeName(file.name);
                      }}
                    />
                  </div>
                </div>

                <div className="max-w-xs">
                  <Label
                    htmlFor="years"
                    className="text-xs uppercase tracking-[0.12em] text-muted-foreground"
                  >
                    Years of experience
                  </Label>
                  <Input
                    id="years"
                    inputMode="numeric"
                    value={years}
                    onChange={(e) => setYears(e.target.value)}
                    placeholder="e.g. 4"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label
                    htmlFor="skills"
                    className="text-xs uppercase tracking-[0.12em] text-muted-foreground"
                  >
                    Key skills
                  </Label>
                  <div className="mt-2 flex flex-wrap items-center gap-2 rounded-lg border border-input bg-card p-2">
                    {skills.map((s) => (
                      <span
                        key={s}
                        className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-[13px] text-foreground"
                      >
                        {s}
                        <button
                          type="button"
                          aria-label={`Remove ${s}`}
                          onClick={() => setSkills((prev) => prev.filter((x) => x !== s))}
                          className="text-muted-foreground hover:text-danger"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                    <input
                      id="skills"
                      value={skillDraft}
                      onChange={(e) => setSkillDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === ",") {
                          e.preventDefault();
                          addSkill();
                        }
                      }}
                      onBlur={addSkill}
                      placeholder={skills.length ? "Add another…" : "Type a skill and press Enter"}
                      className="min-w-[180px] flex-1 bg-transparent px-2 py-1 text-sm outline-none"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 2 && role && (
            <div className="space-y-5">
              <div className="panel p-6 sm:p-8">
                <h2 className="text-2xl text-foreground">Before you begin</h2>
                <dl className="mt-6 grid gap-5 sm:grid-cols-2">
                  {[
                    { k: "Role", v: role.title },
                    { k: "Department", v: role.department },
                    {
                      k: "Format",
                      v: `${DEFAULT_SETTINGS.questionsPerInterview} questions · Digital Chalkboard · no revisiting`,
                    },
                    {
                      k: "Time per question",
                      v: `${DEFAULT_SETTINGS.timerSeconds} seconds, strictly enforced`,
                    },
                    { k: "Experience", v: `${years} year(s)` },
                    { k: "Resume", v: resumeName ?? "—" },
                  ].map((row) => (
                    <div key={row.k}>
                      <dt className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                        {row.k}
                      </dt>
                      <dd className="mt-1 text-[15px] text-foreground">{row.v}</dd>
                    </div>
                  ))}
                </dl>
                <div className="mt-6">
                  <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    Skills declared
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full bg-secondary px-3 py-1 text-[13px] text-foreground"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-warning/40 bg-warning/8 p-5">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-warning">
                  Examination conditions
                </p>
                <p className="report-text mt-2 text-[15px] text-foreground">
                  No external AI tools, browser tabs, or assistance of any kind is permitted.
                  Switching tabs or using unauthorized tools may result in disqualification.
                  Questions are single-pass: once a question closes, it cannot be revisited.
                </p>
              </div>
            </div>
          )}
        </section>

        <div className="mt-8 flex items-center gap-3">
          {step > 0 && (
            <Button variant="outline" onClick={() => setStep((s) => s - 1)}>
              Back
            </Button>
          )}
          {step < STEPS.length - 1 ? (
            <Button onClick={next}>Continue</Button>
          ) : (
            <Button onClick={startInterview} className="bg-emerald hover:bg-emerald/90">
              Start Interview
            </Button>
          )}
        </div>
      </main>
    </div>
  );
}
