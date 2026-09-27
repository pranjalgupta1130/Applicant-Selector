import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export type Submission = {
  mode: "draw" | "equation";
  canvasDataUrl?: string | undefined;
  latex?: string | undefined;
  empty: boolean;
};

export type ChalkboardHandle = {
  getSubmission: () => Submission;
  reset: () => void;
};

const INKS = [
  { name: "Charcoal", value: "#1A1A1A" },
  { name: "Navy", value: "#0B2545" },
  { name: "Emerald", value: "#0F6E56" },
  { name: "Amber", value: "#C9820A" },
];

const WIDTHS = [2, 4, 7];

type Sym = { label: string; snippet: string };
const SYMBOL_GROUPS: { name: string; items: Sym[] }[] = [
  {
    name: "Calculus",
    items: [
      { label: "a⁄b", snippet: "\\frac{a}{b}" },
      { label: "d/dx", snippet: "\\frac{d}{dx}" },
      { label: "∂", snippet: "\\frac{\\partial u}{\\partial x}" },
      { label: "∫", snippet: "\\int_{a}^{b} f(x)\\,dx" },
      { label: "∬", snippet: "\\iint_{A} f\\,dA" },
      { label: "∮", snippet: "\\oint_{C}" },
      { label: "∑", snippet: "\\sum_{i=1}^{n}" },
      { label: "∏", snippet: "\\prod_{i=1}^{n}" },
      { label: "lim", snippet: "\\lim_{x \\to 0}" },
      { label: "∇", snippet: "\\nabla" },
      { label: "∇²", snippet: "\\nabla^2" },
      { label: "ẋ", snippet: "\\dot{x}" },
      { label: "ẍ", snippet: "\\ddot{x}" },
      { label: "∞", snippet: "\\infty" },
    ],
  },
  {
    name: "Algebra",
    items: [
      { label: "xⁿ", snippet: "x^{n}" },
      { label: "xᵢ", snippet: "x_{i}" },
      { label: "√x", snippet: "\\sqrt{x}" },
      { label: "ⁿ√x", snippet: "\\sqrt[n]{x}" },
      { label: "|x|", snippet: "\\left| x \\right|" },
      { label: "eˣ", snippet: "e^{x}" },
      { label: "log", snippet: "\\log_{10}" },
      { label: "ln", snippet: "\\ln" },
      { label: "( )", snippet: "\\left( \\right)" },
      { label: "[ ]", snippet: "\\left[ \\right]" },
      { label: "nCr", snippet: "\\binom{n}{r}" },
      { label: "matrix", snippet: "\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}" },
      { label: "cases", snippet: "\\begin{cases} a & x>0 \\\\ b & x \\le 0 \\end{cases}" },
      { label: "→v", snippet: "\\vec{v}" },
      { label: "x̂", snippet: "\\hat{x}" },
      { label: "x̄", snippet: "\\bar{x}" },
    ],
  },
  {
    name: "Trigonometry",
    items: [
      { label: "sin", snippet: "\\sin\\theta" },
      { label: "cos", snippet: "\\cos\\theta" },
      { label: "tan", snippet: "\\tan\\theta" },
      { label: "cot", snippet: "\\cot\\theta" },
      { label: "sec", snippet: "\\sec\\theta" },
      { label: "csc", snippet: "\\csc\\theta" },
      { label: "sin⁻¹", snippet: "\\sin^{-1}" },
      { label: "cos⁻¹", snippet: "\\cos^{-1}" },
      { label: "tan⁻¹", snippet: "\\tan^{-1}" },
      { label: "sinh", snippet: "\\sinh" },
      { label: "cosh", snippet: "\\cosh" },
      { label: "tanh", snippet: "\\tanh" },
      { label: "°", snippet: "^{\\circ}" },
    ],
  },
  {
    name: "Geometry",
    items: [
      { label: "∠", snippet: "\\angle" },
      { label: "⊥", snippet: "\\perp" },
      { label: "∥", snippet: "\\parallel" },
      { label: "△", snippet: "\\triangle" },
      { label: "≅", snippet: "\\cong" },
      { label: "∼", snippet: "\\sim" },
      { label: "⌒AB", snippet: "\\overset{\\frown}{AB}" },
      { label: "AB̄", snippet: "\\overline{AB}" },
      { label: "□", snippet: "\\square" },
      { label: "○", snippet: "\\bigcirc" },
    ],
  },
  {
    name: "Operators",
    items: [
      { label: "±", snippet: "\\pm" },
      { label: "∓", snippet: "\\mp" },
      { label: "×", snippet: "\\times" },
      { label: "÷", snippet: "\\div" },
      { label: "·", snippet: "\\cdot" },
      { label: "≠", snippet: "\\neq" },
      { label: "≈", snippet: "\\approx" },
      { label: "≡", snippet: "\\equiv" },
      { label: "≤", snippet: "\\leq" },
      { label: "≥", snippet: "\\geq" },
      { label: "≪", snippet: "\\ll" },
      { label: "≫", snippet: "\\gg" },
      { label: "∝", snippet: "\\propto" },
      { label: "→", snippet: "\\rightarrow" },
      { label: "⇒", snippet: "\\Rightarrow" },
      { label: "⇔", snippet: "\\Leftrightarrow" },
      { label: "∈", snippet: "\\in" },
      { label: "∉", snippet: "\\notin" },
      { label: "⊂", snippet: "\\subset" },
      { label: "∪", snippet: "\\cup" },
      { label: "∩", snippet: "\\cap" },
      { label: "∀", snippet: "\\forall" },
      { label: "∃", snippet: "\\exists" },
      { label: "∴", snippet: "\\therefore" },
    ],
  },
  {
    name: "Greek",
    items: "alpha beta gamma delta epsilon zeta eta theta kappa lambda mu nu xi pi rho sigma tau phi chi psi omega Gamma Delta Theta Lambda Pi Sigma Phi Psi Omega"
      .split(" ")
      .map((g) => ({
        label: katexChar(g),
        snippet: `\\${g}`,
      })),
  },
  {
    name: "Letters",
    items: [
      ..."ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map((c) => ({ label: c, snippet: c })),
      ..."abcdefghijklmnopqrstuvwxyz".split("").map((c) => ({ label: c, snippet: c })),
      { label: "ℝ", snippet: "\\mathbb{R}" },
      { label: "ℂ", snippet: "\\mathbb{C}" },
      { label: "ℕ", snippet: "\\mathbb{N}" },
      { label: "ℏ", snippet: "\\hbar" },
      { label: "text", snippet: "\\text{ where }" },
    ],
  },
];

function katexChar(name: string) {
  const map: Record<string, string> = {
    alpha: "α", beta: "β", gamma: "γ", delta: "δ", epsilon: "ε", zeta: "ζ", eta: "η",
    theta: "θ", kappa: "κ", lambda: "λ", mu: "μ", nu: "ν", xi: "ξ", pi: "π", rho: "ρ",
    sigma: "σ", tau: "τ", phi: "φ", chi: "χ", psi: "ψ", omega: "ω", Gamma: "Γ",
    Delta: "Δ", Theta: "Θ", Lambda: "Λ", Pi: "Π", Sigma: "Σ", Phi: "Φ", Psi: "Ψ", Omega: "Ω",
  };
  return map[name] ?? name;
}

type Props = {
  questionKey: string;
  locked?: boolean;
  /** Neurodivergent candidates are steered to the Equation tab first. */
  preferEquation?: boolean;
};

export const Chalkboard = forwardRef<ChalkboardHandle, Props>(function Chalkboard(
  { questionKey, locked = false, preferEquation = false },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const textRef = useRef<HTMLTextAreaElement | null>(null);
  const drawing = useRef(false);
  const last = useRef<{ x: number; y: number } | null>(null);
  const strokes = useRef<ImageData[]>([]);
  const [hasInk, setHasInk] = useState(false);
  const [ink, setInk] = useState(INKS[0]!.value);
  const [width, setWidth] = useState(WIDTHS[1]!);
  const [mode, setMode] = useState<"draw" | "equation">(preferEquation ? "equation" : "draw");
  const [latex, setLatex] = useState("");
  const [group, setGroup] = useState(SYMBOL_GROUPS[0]!.name);

  const paintWhite = (canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  };

  /** Match the bitmap to the on-screen size exactly, keeping existing ink. */
  const sizeCanvas = useCallback((clear = false) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(rect.width * dpr);
    const h = Math.round(rect.height * dpr);
    if (!clear && canvas.width === w && canvas.height === h) return;
    let snapshot: HTMLCanvasElement | null = null;
    if (!clear && canvas.width > 0) {
      snapshot = document.createElement("canvas");
      snapshot.width = canvas.width;
      snapshot.height = canvas.height;
      snapshot.getContext("2d")?.drawImage(canvas, 0, 0);
    }
    canvas.width = w;
    canvas.height = h;
    paintWhite(canvas);
    if (snapshot) canvas.getContext("2d")?.drawImage(snapshot, 0, 0, w, h);
  }, []);

  useEffect(() => {
    sizeCanvas(true);
    strokes.current = [];
    setHasInk(false);
    setLatex("");
    setMode(preferEquation ? "equation" : "draw");
  }, [questionKey, sizeCanvas, preferEquation]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ro = new ResizeObserver(() => sizeCanvas());
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [sizeCanvas, mode]);

  useImperativeHandle(ref, () => ({
    getSubmission: () => {
      if (latex.trim()) return { mode: "equation", latex, empty: false, canvasDataUrl: hasInk ? canvasRef.current?.toDataURL("image/png") : undefined };
      return {
        mode: "draw",
        canvasDataUrl: hasInk ? canvasRef.current?.toDataURL("image/png") : undefined,
        empty: !hasInk,
      };
    },
    reset: () => {
      sizeCanvas(true);
      strokes.current = [];
      setHasInk(false);
      setLatex("");
    },
  }));

  /** Pointer position in bitmap pixels — exact under the pen tip at any zoom or DPR. */
  const pos = (e: { clientX: number; clientY: number }) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * canvas.width,
      y: ((e.clientY - rect.top) / rect.height) * canvas.height,
    };
  };

  const lineWidthFor = (e: React.PointerEvent) => {
    const dpr = window.devicePixelRatio || 1;
    const pressure = e.pointerType === "pen" && e.pressure > 0 ? 0.5 + e.pressure : 1;
    return width * dpr * pressure;
  };

  const start = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (locked) return;
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    e.preventDefault();
    sizeCanvas();
    e.currentTarget.setPointerCapture(e.pointerId);
    strokes.current = [...strokes.current.slice(-19), ctx.getImageData(0, 0, canvas.width, canvas.height)];
    drawing.current = true;
    const p = pos(e);
    last.current = p;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeStyle = ink;
    ctx.fillStyle = ink;
    const lw = lineWidthFor(e);
    ctx.beginPath();
    ctx.arc(p.x, p.y, lw / 2, 0, Math.PI * 2);
    ctx.fill();
    setHasInk(true);
  };

  const move = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current || locked) return;
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const events = e.nativeEvent.getCoalescedEvents?.() ?? [e.nativeEvent];
    ctx.lineWidth = lineWidthFor(e);
    for (const ev of events.length ? events : [e.nativeEvent]) {
      const p = pos(ev);
      const from = last.current ?? p;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
      last.current = p;
    }
  };

  const end = () => {
    drawing.current = false;
    last.current = null;
  };

  const undo = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    const prev = strokes.current.pop();
    if (!canvas || !ctx || !prev) return;
    if (prev.width === canvas.width && prev.height === canvas.height) ctx.putImageData(prev, 0, 0);
    if (strokes.current.length === 0) setHasInk(false);
  };

  const insert = (snippet: string) => {
    const el = textRef.current;
    if (!el) {
      setLatex((p) => `${p}${p ? " " : ""}${snippet}`);
      return;
    }
    const s = el.selectionStart ?? latex.length;
    const eIdx = el.selectionEnd ?? latex.length;
    const pad = s > 0 && latex[s - 1] !== " " && snippet.startsWith("\\") ? " " : "";
    const nextVal = latex.slice(0, s) + pad + snippet + latex.slice(eIdx);
    setLatex(nextVal);
    requestAnimationFrame(() => {
      el.focus();
      const c = s + pad.length + snippet.length;
      el.setSelectionRange(c, c);
    });
  };

  let rendered = "";
  let renderError = "";
  try {
    rendered = latex.trim() ? katex.renderToString(latex, { throwOnError: true, displayMode: true }) : "";
  } catch (err) {
    renderError = err instanceof Error ? err.message : "Could not render this expression";
  }

  const activeGroup = SYMBOL_GROUPS.find((g) => g.name === group) ?? SYMBOL_GROUPS[0]!;

  return (
    <div className="panel overflow-hidden">
      <Tabs value={mode} onValueChange={(v) => setMode(v as "draw" | "equation")}>
        <div className="flex flex-wrap items-center gap-3 border-b border-border bg-secondary/60 px-4 py-3">
          <TabsList className="bg-card">
            <TabsTrigger value="draw">Draw</TabsTrigger>
            <TabsTrigger value="equation">Equation</TabsTrigger>
          </TabsList>
          <span className="ml-auto rounded-full border border-border bg-card px-3 py-1 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            No external tools permitted
          </span>
        </div>

        <TabsContent value="draw" className="m-0 p-4" forceMount hidden={mode !== "draw"}>
          <div className="mb-3 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Pen</span>
              {INKS.map((c) => (
                <button
                  key={c.value}
                  type="button"
                  aria-label={c.name}
                  onClick={() => setInk(c.value)}
                  className={cn(
                    "h-6 w-6 rounded-full border transition-transform",
                    ink === c.value ? "scale-110 border-foreground" : "border-border hover:scale-105",
                  )}
                  style={{ backgroundColor: c.value }}
                />
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Stroke</span>
              {WIDTHS.map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => setWidth(w)}
                  aria-label={`Stroke width ${w}`}
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-md border",
                    width === w ? "border-primary bg-secondary" : "border-border",
                  )}
                >
                  <span className="block rounded-full bg-foreground" style={{ width: w + 2, height: w + 2 }} />
                </button>
              ))}
            </div>
            <div className="ml-auto flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={undo}>
                Undo
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  sizeCanvas(true);
                  strokes.current = [];
                  setHasInk(false);
                }}
              >
                Clear
              </Button>
            </div>
          </div>

          <canvas
            ref={canvasRef}
            onPointerDown={start}
            onPointerMove={move}
            onPointerUp={end}
            onPointerCancel={end}
            className="block h-[320px] w-full cursor-crosshair touch-none rounded-lg border border-border bg-card sm:h-[420px]"
            aria-label="Digital chalkboard — draw your derivation"
          />
          <p className="mt-2 text-xs text-muted-foreground">
            Works with mouse, trackpad, stylus or tablet pen — ink lands exactly under the tip, and pen
            pressure is supported.
          </p>
        </TabsContent>

        <TabsContent value="equation" className="m-0 p-4">
          <div className="mb-2 flex flex-wrap gap-1.5">
            {SYMBOL_GROUPS.map((g) => (
              <button
                key={g.name}
                type="button"
                onClick={() => setGroup(g.name)}
                className={cn(
                  "rounded-full px-3 py-1 text-[12px] font-medium transition-colors",
                  group === g.name ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground",
                )}
              >
                {g.name}
              </button>
            ))}
          </div>
          <div className="mb-3 flex max-h-[132px] flex-wrap gap-1.5 overflow-y-auto rounded-lg border border-border bg-secondary/40 p-2">
            {activeGroup.items.map((q) => (
              <button
                key={q.label + q.snippet}
                type="button"
                disabled={locked}
                onClick={() => insert(q.snippet)}
                title={q.snippet}
                className="min-w-9 rounded-md border border-border bg-card px-2 py-1 text-[14px] text-foreground transition-colors hover:border-emerald hover:text-emerald"
              >
                {q.label}
              </button>
            ))}
          </div>
          <textarea
            ref={textRef}
            value={latex}
            onChange={(e) => setLatex(e.target.value)}
            disabled={locked}
            placeholder="Type your derivation in LaTeX, e.g. \frac{dA}{A} = (M^2 - 1)\frac{dV}{V}"
            className="min-h-[140px] w-full rounded-lg border border-input bg-card p-3 font-mono text-sm text-foreground outline-none focus:border-ring"
          />
          <div className="mt-3 rounded-lg border border-border bg-accent/60 p-4">
            <div className="mb-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Live preview</div>
            {renderError ? (
              <p className="text-sm text-danger">{renderError}</p>
            ) : rendered ? (
              <div className="overflow-x-auto text-foreground" dangerouslySetInnerHTML={{ __html: rendered }} />
            ) : (
              <p className="text-sm text-muted-foreground">Your rendered equation will appear here.</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
});
