import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { animate, stagger } from "animejs";
import hero from "@/assets/boardroom-hero.jpg";

export function BoardroomEntrance() {
  const reduceMotion = useReducedMotion();
  const [visible, setVisible] = useState(true);
  const detailRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reduceMotion) {
      setVisible(false);
      return;
    }

    const details = detailRef.current?.querySelectorAll("[data-entrance-detail]");
    const detailAnimation = details?.length
      ? animate(details, {
          opacity: [0, 1],
          translateY: [10, 0],
          delay: stagger(90),
          duration: 650,
          ease: "out(3)",
        })
      : undefined;
    const timer = window.setTimeout(() => setVisible(false), 1400);

    return () => {
      window.clearTimeout(timer);
      detailAnimation?.cancel();
    };
  }, [reduceMotion]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="fixed inset-0 z-50 overflow-hidden bg-background"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          aria-hidden="true"
        >
          <img
            src={hero}
            alt=""
            width={1600}
            height={912}
            className="absolute inset-0 h-full w-full object-cover"
          />
          <div className="entrance-room-shade absolute inset-0" />

          <div ref={detailRef} className="absolute inset-0 z-20 grid place-items-center px-6 text-center">
            <div className="max-w-lg text-card">
              <p data-entrance-detail className="text-[11px] font-semibold uppercase tracking-[0.2em]">
                DRDO Selection Board
              </p>
              <h1 data-entrance-detail className="mt-4 text-5xl leading-none sm:text-7xl">
                Boardroom AI
              </h1>
              <p data-entrance-detail className="mx-auto mt-4 max-w-sm text-sm leading-relaxed text-card/80">
                Step inside. The panel is ready.
              </p>
            </div>
          </div>

          <motion.div
            className="glass-door glass-door-left absolute inset-y-0 left-0 z-30 w-1/2 origin-left"
            initial={{ x: 0, rotateY: 0 }}
            animate={{ x: "-101%", rotateY: -8 }}
            transition={{ duration: 1.05, delay: 0.3, ease: [0.76, 0, 0.24, 1] }}
          >
            <span className="door-handle door-handle-left" />
          </motion.div>
          <motion.div
            className="glass-door glass-door-right absolute inset-y-0 right-0 z-30 w-1/2 origin-right"
            initial={{ x: 0, rotateY: 0 }}
            animate={{ x: "101%", rotateY: 8 }}
            transition={{ duration: 1.05, delay: 0.3, ease: [0.76, 0, 0.24, 1] }}
          >
            <span className="door-handle door-handle-right" />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}