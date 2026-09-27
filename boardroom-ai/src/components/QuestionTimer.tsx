import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

type Props = {
  /** Changing this key restarts the countdown. */
  questionKey: string;
  seconds: number;
  warningAt: number;
  paused?: boolean;
  onExpire: () => void;
  onTick?: (remaining: number) => void;
};

function format(s: number) {
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

export function QuestionTimer({
  questionKey,
  seconds,
  warningAt,
  paused = false,
  onExpire,
  onTick,
}: Props) {
  const [remaining, setRemaining] = useState(seconds);
  const expired = useRef(false);

  useEffect(() => {
    setRemaining(seconds);
    expired.current = false;
  }, [questionKey, seconds]);

  useEffect(() => {
    if (paused) return;
    const id = window.setInterval(() => {
      setRemaining((prev) => {
        const next = prev - 1;
        if (next <= 0) {
          if (!expired.current) {
            expired.current = true;
            onExpire();
          }
          return 0;
        }
        onTick?.(next);
        return next;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [paused, onExpire, onTick, questionKey]);

  const warning = remaining <= warningAt && remaining > 0;
  const progress = Math.max(0, Math.min(1, remaining / seconds));

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-full border bg-card px-4 py-2 shadow-surface",
        warning ? "border-warning/50 timer-pulse" : "border-border",
      )}
      role="timer"
      aria-live="off"
    >
      <svg viewBox="0 0 36 36" className="h-9 w-9 -rotate-90" aria-hidden="true">
        <circle cx="18" cy="18" r="15.5" fill="none" strokeWidth="3" className="stroke-secondary" />
        <circle
          cx="18"
          cy="18"
          r="15.5"
          fill="none"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={2 * Math.PI * 15.5}
          strokeDashoffset={(1 - progress) * 2 * Math.PI * 15.5}
          className={cn(
            "transition-[stroke-dashoffset] duration-1000 ease-linear",
            warning ? "stroke-warning" : "stroke-primary",
          )}
        />
      </svg>
      <div className="leading-tight">
        <div
          className={cn(
            "font-display text-xl tabular-nums",
            warning ? "text-warning" : "text-primary",
          )}
        >
          {format(remaining)}
        </div>
        <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
          {warning ? "Time running out" : "Time for this question"}
        </div>
      </div>
    </div>
  );
}
