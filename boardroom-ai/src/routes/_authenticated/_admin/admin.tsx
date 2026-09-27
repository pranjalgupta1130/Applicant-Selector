import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { BoardHeader } from "@/components/BoardHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DEFAULT_SETTINGS,
  QUESTION_BANK,
  ROLES,
  type InterviewStage,
  type Question,
  type Role,
} from "@/lib/interview-data";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/_admin/admin")({
  head: () => ({
    meta: [
      { title: "Administration — Boardroom AI" },
      {
        name: "description",
        content:
          "Manage the DRDO question bank, open roles, interview length, timer thresholds and evaluation rubric weights.",
      },
      { property: "og:title", content: "Administration — Boardroom AI" },
      {
        property: "og:description",
        content: "Question bank, roles and interview settings for Boardroom AI.",
      },
    ],
  }),
  component: Admin,
});

const STAGES: InterviewStage[] = [
  "Ice-breaker",
  "Fundamentals",
  "Technical",
  "Deep-dive",
  "Scenario",
];
const DIFFICULTIES: Question["difficulty"][] = ["Easy", "Moderate", "Hard"];

function Admin() {
  return (
    <div className="min-h-screen bg-background">
      <BoardHeader />
      <main className="mx-auto max-w-6xl px-5 pb-20 pt-8 sm:px-8">
        <h1 className="text-3xl text-foreground sm:text-4xl">Administration</h1>
        <p className="report-text mt-2 max-w-2xl text-[15px] text-muted-foreground">
          Configure what the panel asks, which posts are open, and how strictly the session is timed.
        </p>

        <Tabs defaultValue="questions" className="mt-8">
          <TabsList className="bg-secondary">
            <TabsTrigger value="questions">Question Bank</TabsTrigger>
            <TabsTrigger value="roles">Roles</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="questions" className="mt-6">
            <QuestionBank />
          </TabsContent>
          <TabsContent value="roles" className="mt-6">
            <RolesTab />
          </TabsContent>
          <TabsContent value="settings" className="mt-6">
            <SettingsTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function QuestionBank() {
  const [questions, setQuestions] = useState<Question[]>(QUESTION_BANK);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState({
    text: "",
    roleId: ROLES[0]!.id,
    stage: STAGES[1]! as InterviewStage,
    difficulty: "Moderate" as Question["difficulty"],
  });

  const save = () => {
    if (draft.text.trim().length < 15) {
      toast.error("Write the full question (at least 15 characters).");
      return;
    }
    if (editingId) {
      setQuestions((prev) =>
        prev.map((q) => (q.id === editingId ? { ...q, ...draft, text: draft.text.trim() } : q)),
      );
      toast.success("Question updated.");
    } else {
      setQuestions((prev) => [
        { id: `q-${Date.now()}`, ...draft, text: draft.text.trim() },
        ...prev,
      ]);
      toast.success("Question added to the bank.");
    }
    setEditingId(null);
    setDraft({ text: "", roleId: ROLES[0]!.id, stage: STAGES[1]!, difficulty: "Moderate" });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
      <div className="space-y-3">
        {questions.map((q) => (
          <article key={q.id} className="panel p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-primary/8 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">
                {q.stage}
              </span>
              <span className="rounded-full bg-secondary px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                {q.difficulty}
              </span>
              <span className="text-[12px] text-emerald">
                {ROLES.find((r) => r.id === q.roleId)?.title ?? "Unassigned"}
              </span>
              <div className="ml-auto flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingId(q.id);
                    setDraft({
                      text: q.text,
                      roleId: q.roleId,
                      stage: q.stage,
                      difficulty: q.difficulty,
                    });
                  }}
                >
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-danger"
                  onClick={() => {
                    setQuestions((prev) => prev.filter((x) => x.id !== q.id));
                    toast.success("Question removed.");
                  }}
                >
                  Delete
                </Button>
              </div>
            </div>
            <p className="report-text mt-3 text-[15px] text-foreground">{q.text}</p>
          </article>
        ))}
      </div>

      <aside className="panel h-fit p-5 lg:sticky lg:top-28">
        <h2 className="text-xl text-foreground">{editingId ? "Edit question" : "Add question"}</h2>
        <div className="mt-4 space-y-4">
          <div>
            <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
              Question
            </Label>
            <textarea
              value={draft.text}
              onChange={(e) => setDraft((d) => ({ ...d, text: e.target.value }))}
              className="mt-2 min-h-[120px] w-full rounded-lg border border-input bg-card p-3 text-sm outline-none focus:border-ring"
              placeholder="Derive…"
            />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">Role</Label>
            <select
              value={draft.roleId}
              onChange={(e) => setDraft((d) => ({ ...d, roleId: e.target.value }))}
              className="mt-2 w-full rounded-lg border border-input bg-card p-2.5 text-sm outline-none focus:border-ring"
            >
              {ROLES.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Stage
              </Label>
              <select
                value={draft.stage}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, stage: e.target.value as InterviewStage }))
                }
                className="mt-2 w-full rounded-lg border border-input bg-card p-2.5 text-sm outline-none focus:border-ring"
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Difficulty
              </Label>
              <select
                value={draft.difficulty}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    difficulty: e.target.value as Question["difficulty"],
                  }))
                }
                className="mt-2 w-full rounded-lg border border-input bg-card p-2.5 text-sm outline-none focus:border-ring"
              >
                {DIFFICULTIES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <Button onClick={save} className="w-full bg-emerald hover:bg-emerald/90">
            {editingId ? "Save changes" : "Add to question bank"}
          </Button>
          {editingId && (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setEditingId(null);
                setDraft({
                  text: "",
                  roleId: ROLES[0]!.id,
                  stage: STAGES[1]!,
                  difficulty: "Moderate",
                });
              }}
            >
              Cancel
            </Button>
          )}
        </div>
      </aside>
    </div>
  );
}

function RolesTab() {
  const [roles, setRoles] = useState<Role[]>(ROLES);
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [openings, setOpenings] = useState("1");

  const add = () => {
    if (title.trim().length < 4 || department.trim().length < 3) {
      toast.error("Enter both a role title and a department.");
      return;
    }
    const n = Number(openings);
    if (!Number.isInteger(n) || n < 1) {
      toast.error("Openings must be a whole number of at least 1.");
      return;
    }
    setRoles((prev) => [
      {
        id: `role-${Date.now()}`,
        title: title.trim(),
        department: department.trim(),
        openings: n,
        summary: "Newly opened post.",
      },
      ...prev,
    ]);
    setTitle("");
    setDepartment("");
    setOpenings("1");
    toast.success("Role opened.");
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
      <div className="space-y-3">
        {roles.map((r) => (
          <div key={r.id} className="panel flex flex-wrap items-center gap-4 p-5">
            <div className="min-w-[200px] flex-1">
              <h3 className="text-lg text-foreground">{r.title}</h3>
              <p className="text-[13px] text-emerald">{r.department}</p>
            </div>
            <div className="flex items-center gap-2">
              <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Openings
              </Label>
              <Input
                value={String(r.openings)}
                inputMode="numeric"
                onChange={(e) =>
                  setRoles((prev) =>
                    prev.map((x) =>
                      x.id === r.id ? { ...x, openings: Math.max(0, Number(e.target.value) || 0) } : x,
                    ),
                  )
                }
                className="w-20"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-danger"
              onClick={() => {
                setRoles((prev) => prev.filter((x) => x.id !== r.id));
                toast.success("Role closed.");
              }}
            >
              Close role
            </Button>
          </div>
        ))}
      </div>

      <aside className="panel h-fit p-5">
        <h2 className="text-xl text-foreground">Open a new role</h2>
        <div className="mt-4 space-y-4">
          <div>
            <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
              Role title
            </Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Scientist 'B' — Propulsion"
              className="mt-2"
            />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
              Department
            </Label>
            <Input
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="Gas Turbine Research (GTRE)"
              className="mt-2"
            />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
              Openings
            </Label>
            <Input
              value={openings}
              inputMode="numeric"
              onChange={(e) => setOpenings(e.target.value)}
              className="mt-2 w-24"
            />
          </div>
          <Button onClick={add} className="w-full bg-emerald hover:bg-emerald/90">
            Open role
          </Button>
        </div>
      </aside>
    </div>
  );
}

const WEIGHT_KEYS = ["Technical Correctness", "Completeness", "Communication", "Problem Solving"];

function SettingsTab() {
  const [length, setLength] = useState(DEFAULT_SETTINGS.questionsPerInterview);
  const [timer, setTimer] = useState(DEFAULT_SETTINGS.timerSeconds);
  const [warn, setWarn] = useState(DEFAULT_SETTINGS.warningThresholdSeconds);
  const [weights, setWeights] = useState<Record<string, number>>(DEFAULT_SETTINGS.rubricWeights);

  const total = WEIGHT_KEYS.reduce((sum, k) => sum + (weights[k] ?? 0), 0);

  const save = () => {
    if (total !== 100) {
      toast.error(`Rubric weights must sum to 100% — currently ${total}%.`);
      return;
    }
    if (warn >= timer) {
      toast.error("The warning threshold must be shorter than the per-question time.");
      return;
    }
    toast.success("Interview settings saved.");
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="panel p-6">
        <h2 className="text-xl text-foreground">Interview format</h2>
        <div className="mt-6 space-y-8">
          <div>
            <div className="flex items-baseline justify-between">
              <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Questions per interview
              </Label>
              <span className="font-display text-xl tabular-nums text-primary">{length}</span>
            </div>
            <Slider
              value={[length]}
              min={3}
              max={12}
              step={1}
              onValueChange={([v]) => setLength(v ?? length)}
              className="mt-3"
            />
          </div>
          <div>
            <div className="flex items-baseline justify-between">
              <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Time per question
              </Label>
              <span className="font-display text-xl tabular-nums text-primary">{timer}s</span>
            </div>
            <Slider
              value={[timer]}
              min={30}
              max={300}
              step={15}
              onValueChange={([v]) => setTimer(v ?? timer)}
              className="mt-3"
            />
          </div>
          <div>
            <div className="flex items-baseline justify-between">
              <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Warning threshold
              </Label>
              <span className="font-display text-xl tabular-nums text-warning">{warn}s left</span>
            </div>
            <Slider
              value={[warn]}
              min={5}
              max={60}
              step={5}
              onValueChange={([v]) => setWarn(v ?? warn)}
              className="mt-3"
            />
          </div>
        </div>
      </div>

      <div className="panel p-6">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl text-foreground">Evaluation rubric weights</h2>
          <span
            className={cn(
              "font-display text-xl tabular-nums",
              total === 100 ? "text-emerald" : "text-danger",
            )}
          >
            {total}%
          </span>
        </div>
        <div className="mt-6 space-y-7">
          {WEIGHT_KEYS.map((k) => (
            <div key={k}>
              <div className="flex items-baseline justify-between">
                <Label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                  {k}
                </Label>
                <span className="text-sm tabular-nums text-foreground">{weights[k] ?? 0}%</span>
              </div>
              <Slider
                value={[weights[k] ?? 0]}
                min={0}
                max={100}
                step={5}
                onValueChange={([v]) => setWeights((prev) => ({ ...prev, [k]: v ?? 0 }))}
                className="mt-3"
              />
            </div>
          ))}
        </div>
        {total !== 100 && (
          <p className="mt-5 rounded-lg border border-danger/30 bg-danger/8 px-4 py-3 text-[13px] text-danger">
            Weights must sum to exactly 100% before settings can be saved.
          </p>
        )}
        <Button onClick={save} className="mt-6 w-full bg-emerald hover:bg-emerald/90">
          Save settings
        </Button>
      </div>
    </div>
  );
}
