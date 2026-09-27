import { useEffect, useState } from "react";
import { Pause, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const SPEEDS = [0.75, 1, 1.25] as const;

export function QuestionReadAloud({ question, questionKey }: { question: string; questionKey: string }) {
  const [speed, setSpeed] = useState<(typeof SPEEDS)[number]>(1);
  const [speaking, setSpeaking] = useState(false);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
    return () => window.speechSynthesis.cancel();
  }, [questionKey, supported]);

  const toggle = () => {
    if (!supported) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(question);
    utterance.lang = "en-IN";
    utterance.rate = speed;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setSpeaking(true);
  };

  return (
    <div className="flex flex-wrap items-center gap-2" aria-label="Question read aloud controls">
      <Button type="button" variant="outline" size="sm" onClick={toggle} disabled={!supported} aria-label={speaking ? "Stop reading question" : "Read question aloud"}>
        {speaking ? <Pause /> : <Volume2 />}
        {speaking ? "Stop" : "Read aloud"}
      </Button>
      <div className="flex h-8 overflow-hidden rounded-md border border-input bg-background" aria-label="Reading speed">
        {SPEEDS.map((value) => (
          <Button
            key={value}
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              if (speaking) window.speechSynthesis.cancel();
              setSpeaking(false);
              setSpeed(value);
            }}
            aria-pressed={speed === value}
            className={cn("h-full rounded-none border-r border-input px-2.5 last:border-r-0", speed === value && "bg-accent text-accent-foreground")}
          >
            {value}×
          </Button>
        ))}
      </div>
    </div>
  );
}