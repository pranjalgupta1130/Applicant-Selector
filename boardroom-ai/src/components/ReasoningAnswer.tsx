import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type ReasoningHandle = {
  get: () => { text: string; spoken: boolean; empty: boolean };
};

type SpeechRec = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  onresult: ((e: { resultIndex: number; results: ArrayLike<ArrayLike<{ transcript: string; confidence: number }> & { isFinal: boolean }> }) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: { error: string }) => void) | null;
};

/** Normalise spacing, stray repeats ("the the") and the spoken "i" pronoun. */
function tidy(t: string) {
  return t
    .replace(/\s+/g, " ")
    .replace(/\b(\w+)( \1\b)+/gi, "$1")
    .replace(/\bi\b/g, "I")
    .replace(/\s+([,.?!])/g, "$1")
    .trim();
}

/** Typing space with voice dictation for theory/reasoning questions. */
export const ReasoningAnswer = forwardRef<
  ReasoningHandle,
  { questionKey: string; onPasteBlocked?: () => void; onTypingBurst?: () => void }
>(function ReasoningAnswer({ questionKey, onPasteBlocked, onTypingBurst }, ref) {
  const [text, setText] = useState("");
  const [interim, setInterim] = useState("");
  const [listening, setListening] = useState(false);
  const [spoken, setSpoken] = useState(false);
  const [supported, setSupported] = useState(true);
  const rec = useRef<SpeechRec | null>(null);
  const committed = useRef<Set<number>>(new Set());
  const wantOn = useRef(false);

  useEffect(() => {
    setText("");
    setInterim("");
    setSpoken(false);
    stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionKey]);

  useEffect(() => {
    const W = window as unknown as { SpeechRecognition?: new () => SpeechRec; webkitSpeechRecognition?: new () => SpeechRec };
    const Ctor = W.SpeechRecognition ?? W.webkitSpeechRecognition;
    if (!Ctor) {
      setSupported(false);
      return;
    }
    const r = new Ctor();
    r.lang = "en-IN"; // Indian English — keeps Hinglish/regional words recognisable
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 3;
    r.onresult = (e) => {
      let live = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i]!;
        if (res.isFinal) {
          // Each final segment is committed exactly once (mobile browsers re-send old results).
          if (committed.current.has(i)) continue;
          committed.current.add(i);
          let best = res[0]!;
          for (let a = 1; a < res.length; a++) if ((res[a]!.confidence ?? 0) > (best.confidence ?? 0)) best = res[a]!;
          const seg = tidy(best.transcript);
          if (!seg) continue;
          setText((p) => {
            if (p.trim().toLowerCase().endsWith(seg.toLowerCase())) return p; // duplicate echo
            const sentenceStart = !p.trim() || /[.?!]$/.test(p.trim());
            const piece = sentenceStart ? seg.charAt(0).toUpperCase() + seg.slice(1) : seg;
            return `${p}${p && !p.endsWith(" ") ? " " : ""}${piece}`;
          });
        } else live += res[0]!.transcript;
      }
      setInterim(tidy(live));
    };
    r.onend = () => {
      committed.current = new Set(); // result indices restart with each session
      if (wantOn.current) {
        try { r.start(); } catch { /* already running */ }
      } else setListening(false);
    };
    r.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "audio-capture") {
        wantOn.current = false;
        setListening(false);
      }
    };
    rec.current = r;
    return () => {
      wantOn.current = false;
      try { r.stop(); } catch { /* noop */ }
    };
  }, []);

  function stop() {
    wantOn.current = false;
    try { rec.current?.stop(); } catch { /* noop */ }
    setListening(false);
    setInterim("");
  }

  const toggle = () => {
    if (listening) return stop();
    if (!rec.current) return;
    wantOn.current = true;
    setSpoken(true);
    try { rec.current.start(); } catch { /* already running */ }
    setListening(true);
  };

  useImperativeHandle(ref, () => ({
    get: () => {
      const full = `${text} ${interim}`.trim();
      return { text: full, spoken, empty: full.length === 0 };
    },
  }));

  return (
    <div className="panel overflow-hidden">
      <div className="flex flex-wrap items-center gap-3 border-b border-border bg-secondary/60 px-4 py-3">
        <span className="text-[13px] font-medium text-foreground">Written or spoken answer</span>
        <span className="ml-auto rounded-full border border-border bg-card px-3 py-1 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          No external tools permitted
        </span>
      </div>
      <div className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <Button type="button" onClick={toggle} disabled={!supported} variant={listening ? "destructive" : "outline"} className="gap-2">
            <span className={cn("h-2.5 w-2.5 rounded-full", listening ? "animate-pulse bg-destructive-foreground" : "bg-danger")} />
            {listening ? "Stop speaking" : "Speak your answer"}
          </Button>
          <p className="text-[13px] text-muted-foreground">
            {supported
              ? listening
                ? "Listening… speak naturally; your words are transcribed below."
                : "Type below, or press speak and explain aloud as you would to the board."
              : "Voice input isn't supported in this browser — please type your answer."}
          </p>
        </div>
        <textarea
          value={text}
          onChange={(e) => {
            const added = e.target.value.length - text.length;
            if (added > 60 && !listening) onTypingBurst?.();
            setText(e.target.value);
          }}
          onPaste={(e) => {
            e.preventDefault();
            onPasteBlocked?.();
          }}
          onDrop={(e) => e.preventDefault()}
          spellCheck={false}
          placeholder="Explain your reasoning in your own words…"
          className="report-text min-h-[220px] w-full rounded-lg border border-input bg-card p-4 text-[15px] text-foreground outline-none focus:border-ring"
        />
        {interim && <p className="report-text mt-2 text-[14px] italic text-muted-foreground">{interim}</p>}
      </div>
    </div>
  );
});
