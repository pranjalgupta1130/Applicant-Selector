import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { useServerFn } from "@tanstack/react-start";
import { toast } from "sonner";
import { lovable } from "@/integrations/lovable/index";
import { supabase } from "@/integrations/supabase/client";
import { claimAdmin } from "@/lib/interview.functions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import blueprint from "@/assets/auth-blueprint.jpg";
import { BrandLogo } from "@/components/BrandLogo";
import { MotionReveal } from "@/components/MotionReveal";
import { ScientistQuote } from "@/components/ScientistQuote";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in — Boardroom AI" },
      { name: "description", content: "Sign in to Boardroom AI as a DRDO candidate or selection panel member." },
      { property: "og:title", content: "Sign in — Boardroom AI" },
      { property: "og:description", content: "Candidate and panel staff sign-in for the DRDO interview simulation." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: AuthPage,
});

const CODE_KEY = "boardroom.staffCode";
const MODE_KEY = "boardroom.signInMode";

function AuthPage() {
  const navigate = useNavigate();
  const redeem = useServerFn(claimAdmin);
  const [as, setAs] = useState<"candidate" | "staff">("candidate");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [existing, setExisting] = useState<string | null>(null);
  const finishing = useRef(false);

  /** Route a signed-in user according to the chosen mode; redeem the staff code first if given. */
  const finish = useCallback(
    async (mode: "candidate" | "staff", staffCode: string | null) => {
      if (finishing.current) return;
      finishing.current = true;
      setBusy(true);
      try {
        const { data, error: userError } = await supabase.auth.getUser();
        if (userError || !data.user) throw new Error("Your Google session could not be verified.");

        const { error: profileError } = await supabase.rpc("ensure_profile");
        if (profileError) throw profileError;

        if (mode === "staff" && staffCode) {
          const res = await redeem({ data: { code: staffCode } });
          if (!res.ok) {
            toast.error(res.message);
            setExisting(data.user.email ?? "your account");
            return;
          }
          toast.success("Panel staff access granted.");
        }

        const { data: isAdmin, error: roleError } = await supabase.rpc("has_role", { _user_id: data.user.id, _role: "admin" });
        if (roleError) throw roleError;
        if (mode === "staff" && !isAdmin) {
          toast.error("This account does not have panel staff access. Enter a valid staff code.");
          setExisting(data.user.email ?? "your account");
          return;
        }

        sessionStorage.removeItem(MODE_KEY);
        sessionStorage.removeItem(CODE_KEY);
        if (mode !== "staff" && isAdmin) toast.info("This account is registered as panel staff, so you are signed in to the panel.");
        await navigate({ to: isAdmin ? "/panel" : "/dashboard", replace: true });
      } catch (error) {
        console.error("Authentication handoff failed", error);
        toast.error(error instanceof Error ? error.message : "Could not finish signing in. Please try again.");
      } finally {
        finishing.current = false;
        setBusy(false);
      }
    },
    [navigate, redeem],
  );

  /** Continue once after Google's public callback; existing users can choose their destination. */
  useEffect(() => {
    const resume = async () => {
      const mode = sessionStorage.getItem(MODE_KEY) as "candidate" | "staff" | null;
      if (!mode) return false;
      const pending = sessionStorage.getItem(CODE_KEY);
      await finish(mode, pending);
      return true;
    };
    void supabase.auth.getUser().then(async ({ data }) => {
      if (!data.user) return;
      if (!(await resume())) setExisting(data.user.email ?? "your account");
    });
  }, [finish]);

  const switchAccount = async () => {
    await supabase.auth.signOut({ scope: "local" });
    sessionStorage.removeItem(MODE_KEY);
    sessionStorage.removeItem(CODE_KEY);
    setExisting(null);
    setBusy(false);
  };

  const signIn = async () => {
    if (as === "staff" && !code.trim()) {
      toast.error("Enter your DRDO staff invite code.");
      return;
    }
    if (existing) {
      await finish(as, as === "staff" ? code.trim() : null);
      return;
    }
    sessionStorage.setItem(MODE_KEY, as);
    if (as === "staff") sessionStorage.setItem(CODE_KEY, code.trim());
    else sessionStorage.removeItem(CODE_KEY);
    setBusy(true);
    try {
      const result = await lovable.auth.signInWithOAuth("google", { redirect_uri: window.location.origin + "/auth" });
      if (result.error) throw result.error;
      if (!result.redirected) await finish(as, as === "staff" ? code.trim() : null);
    } catch (error) {
      console.error("Google sign-in failed", error);
      sessionStorage.removeItem(MODE_KEY);
      sessionStorage.removeItem(CODE_KEY);
      setBusy(false);
      toast.error("Google sign-in did not complete. Please try again.");
    }
  };

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-primary lg:block">
        <img src={blueprint} alt="Blueprint drawings of a missile, radar dish and orbital paths" width={1024} height={1280} className="absolute inset-0 h-full w-full object-cover opacity-90" />
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
          <h1 className="text-4xl text-foreground">Sign in to continue</h1>
          <p className="report-text mt-2 text-[15px] text-muted-foreground">
            Choose how you are joining today. Candidates take the interview; panel staff review evaluations and manage the question bank.
          </p>

          {existing && (
            <div className="mt-5 flex items-center justify-between gap-4 rounded-md border border-border bg-muted/40 px-4 py-3">
              <div className="min-w-0">
                <p className="text-xs font-medium text-foreground">Signed in as</p>
                <p className="truncate text-xs text-muted-foreground">{existing}</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={switchAccount} disabled={busy}>
                Change account
              </Button>
            </div>
          )}

          <div className="mt-8 grid grid-cols-2 gap-3">
            {([
              { id: "candidate", title: "Candidate", desc: "Sit the interview" },
              { id: "staff", title: "Panel staff", desc: "Review & administer" },
            ] as const).map((o) => (
              <button
                key={o.id}
                type="button"
                onClick={() => setAs(o.id)}
                aria-pressed={as === o.id}
                className={cn(
                  "panel p-4 text-left transition-all",
                  as === o.id ? "border-primary ring-2 ring-primary/20" : "hover:shadow-raised",
                )}
              >
                <div className="font-display text-xl text-foreground">{o.title}</div>
                <div className="text-[13px] text-muted-foreground">{o.desc}</div>
              </button>
            ))}
          </div>

          {as === "staff" && (
            <div className="mt-5">
              <Label htmlFor="code" className="text-xs uppercase tracking-[0.12em] text-muted-foreground">
                Staff invite code
              </Label>
              <Input id="code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="Issued by DRDO recruitment cell" className="mt-2" />
            </div>
          )}

          <Button onClick={signIn} disabled={busy} className="mt-6 h-11 w-full gap-3" size="lg">
            <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
              <path fill="currentColor" d="M21.35 11.1H12v2.9h5.35c-.23 1.5-1.7 4.4-5.35 4.4a5.9 5.9 0 0 1 0-11.8c1.8 0 3 .77 3.7 1.43l2.5-2.4C16.6 4.1 14.5 3.2 12 3.2a8.8 8.8 0 1 0 0 17.6c5.1 0 8.45-3.58 8.45-8.62 0-.58-.06-1.02-.1-1.08Z" />
            </svg>
            {busy ? "Signing you in…" : existing ? `Continue as ${as === "staff" ? "panel staff" : "candidate"}` : "Continue with Google"}
          </Button>
          <p className="mt-4 text-center text-[12px] text-muted-foreground">
            By continuing you agree to camera proctoring during the interview.
          </p>
        </MotionReveal>
      </div>
    </div>
  );
}
