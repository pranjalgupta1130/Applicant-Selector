import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { setLocalUser, DEMO_USERS, type LocalRole } from "@/lib/local-auth";
import { Button } from "@/components/ui/button";
import { BrandLogo } from "@/components/BrandLogo";
import { MotionReveal } from "@/components/MotionReveal";
import blueprint from "@/assets/auth-blueprint.jpg";
import { ScientistQuote } from "@/components/ScientistQuote";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in — Boardroom AI" },
      {
        name: "description",
        content: "Local BoardRoom AI interview simulation",
      },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(DEMO_USERS[0].id);
  const [role, setRole] = useState<LocalRole>("candidate");
  const [busy, setBusy] = useState(false);

  const candidates = DEMO_USERS.filter((u) => u.role === "candidate");
  const users = role === "candidate"
    ? candidates
    : DEMO_USERS.filter((u) => u.role === "admin");

  const signIn = async () => {
    const user = users.find((u) => u.id === selected);
    if (!user) return;

    setBusy(true);

    setLocalUser(user);
    window.dispatchEvent(new Event("boardroom-auth-changed"));

    await new Promise((resolve) => setTimeout(resolve, 250));

    await navigate({
      to: user.role === "admin" ? "/panel" : "/dashboard",
      replace: true,
    });

    setBusy(false);
  };

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-primary lg:block">
        <img
          src={blueprint}
          alt="Blueprint drawings of a missile, radar dish and orbital paths"
          width={1024}
          height={1280}
          className="absolute inset-0 h-full w-full object-cover opacity-90"
        />

        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-primary via-primary/70 to-transparent p-12">
          <ScientistQuote className="font-display text-4xl leading-tight text-primary-foreground" />
        </div>
      </div>

      <div className="flex flex-col px-6 py-10 sm:px-12">
        <div>
          <BrandLogo animateMark />
          <div className="table-edge mt-4" />
        </div>

        <MotionReveal className="mx-auto my-auto w-full max-w-md py-12">
          <h1 className="text-4xl text-foreground">
            Local Demo Access
          </h1>

          <p className="report-text mt-2 text-[15px] text-muted-foreground">
            Select a demo identity to enter the BoardRoom AI interview
            simulation. No Supabase or external authentication is required.
          </p>

          <div className="mt-8 grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => {
                setRole("candidate");
                setSelected(candidates[0].id);
              }}
              className={`panel p-4 text-left ${
                role === "candidate"
                  ? "border-primary ring-2 ring-primary/20"
                  : "hover:shadow-raised"
              }`}
            >
              <div className="font-display text-xl text-foreground">
                Candidate
              </div>
              <div className="text-[13px] text-muted-foreground">
                Take the interview
              </div>
            </button>

            <button
              type="button"
              onClick={() => {
                setRole("admin");
                setSelected("demo-panel");
              }}
              className={`panel p-4 text-left ${
                role === "admin"
                  ? "border-primary ring-2 ring-primary/20"
                  : "hover:shadow-raised"
              }`}
            >
              <div className="font-display text-xl text-foreground">
                Panel Staff
              </div>
              <div className="text-[13px] text-muted-foreground">
                Review results
              </div>
            </button>
          </div>

          <div className="mt-6">
            <label className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
              Demo Identity
            </label>

            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="mt-2 w-full rounded-md border border-input bg-background px-3 py-3 text-sm text-foreground"
            >
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name} — {user.email}
                </option>
              ))}
            </select>
          </div>

          <Button
            onClick={signIn}
            disabled={busy}
            className="mt-6 h-11 w-full"
            size="lg"
          >
            {busy ? "Entering BoardRoom…" : "Enter BoardRoom"}
          </Button>

          <p className="mt-4 text-center text-[12px] text-muted-foreground">
            Local demo mode • React ? Node ? Python AI
          </p>
        </MotionReveal>
      </div>
    </div>
  );
}
