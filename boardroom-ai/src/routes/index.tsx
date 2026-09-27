import { createFileRoute, Link } from "@tanstack/react-router";
import { BoardHeader } from "@/components/BoardHeader";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import hero from "@/assets/boardroom-hero.jpg";
import { MotionReveal } from "@/components/MotionReveal";
import { BoardroomEntrance } from "@/components/BoardroomEntrance";
import { ScientistQuote } from "@/components/ScientistQuote";
import { ArrowRight } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Boardroom AI — DRDO panel interview simulation" },
      {
        name: "description",
        content:
          "Practise the DRDO selection-board interview: timed single-pass questions, smart follow-ups, a digital chalkboard, voice answers and camera proctoring.",
      },
      { property: "og:title", content: "Boardroom AI — DRDO panel interview simulation" },
      { property: "og:description", content: "Timed questions, smart follow-ups, chalkboard and voice answers, proctored like the real board." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Landing,
});

function Landing() {
  const { user, isAdmin } = useAuth();
  const dest = isAdmin ? "/panel" : "/dashboard";
  return (
    <div className="min-h-screen bg-background">
      <BoardroomEntrance />
      <BoardHeader />
      <main>
        <section className="relative h-[calc(100svh-84px)] min-h-[600px] overflow-hidden">
          <img src={hero} alt="Bright executive boardroom with a long oak table and a whiteboard of equations" width={1600} height={912} className="absolute inset-0 h-full w-full object-cover" />
          <div className="landing-photo-shade absolute inset-0" />
          <div className="relative mx-auto flex h-full max-w-7xl items-end px-5 pb-10 pt-24 sm:px-8 sm:pb-14">
            <MotionReveal className="max-w-2xl text-card">
              <ScientistQuote className="max-w-xl font-display text-xl leading-snug text-card/90 sm:text-2xl" />
              <h1 className="mt-5 text-5xl leading-[0.98] sm:text-7xl">Boardroom AI</h1>
              <p className="mt-5 max-w-xl font-display text-2xl leading-snug sm:text-3xl">Your thinking, across the table.</p>
              <p className="mt-5 max-w-lg text-[15px] leading-relaxed text-card/85 sm:text-base">
                A focused DRDO interview simulation built around how you explain, derive and respond under pressure.
              </p>
              <div className="mt-8">
                <Button asChild size="lg" variant="secondary">
                  <Link to={user ? dest : "/auth"} className="group">
                    {user ? "Go to my dashboard" : "Enter the boardroom"}
                    <ArrowRight className="transition-transform duration-300 group-hover:translate-x-1" />
                  </Link>
                </Button>
              </div>
            </MotionReveal>
          </div>
        </section>

      </main>
    </div>
  );
}
