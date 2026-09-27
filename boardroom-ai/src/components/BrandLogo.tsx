import { useEffect, useRef } from "react";
import { animate } from "animejs";
import logo from "@/assets/boardroom-logo-panel.png";
import { cn } from "@/lib/utils";

type BrandLogoProps = {
  compact?: boolean;
  animateMark?: boolean;
  className?: string;
};

export function BrandLogo({ compact = false, animateMark = false, className }: BrandLogoProps) {
  const markRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!animateMark || !markRef.current || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const animation = animate(markRef.current, {
      opacity: [0, 1],
      scale: [0.88, 1],
      rotate: [-2, 0],
      duration: 700,
      ease: "out(3)",
    });
    return () => {
      animation.cancel();
    };
  }, [animateMark]);

  return (
    <span className={cn("flex min-w-0 items-center gap-3", className)}>
      <span className={cn("grid shrink-0 place-items-center overflow-hidden rounded-md border border-primary/15 bg-card shadow-surface", compact ? "h-9 w-9" : "h-11 w-11")}>
        <img
          ref={markRef}
          src={logo}
          alt=""
          width={1024}
          height={1024}
          className="h-full w-full object-contain p-1"
        />
      </span>
      <span className="min-w-0">
        <span className={cn("block truncate font-display leading-none text-primary", compact ? "text-2xl" : "text-3xl")}>Boardroom AI</span>
        <span className="mt-1 block truncate text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">DRDO Interview Simulation</span>
      </span>
    </span>
  );
}