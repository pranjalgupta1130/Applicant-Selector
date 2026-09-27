import type { Json } from "@/integrations/supabase/types";

export type FinalReport = {
  name: string;
  roleTitle: string;
  date: string;
  status: string;
  overallScore: number | null;
  rubric: { label: string; score: number }[];
  covered: string[];
  missing: string[];
  reasoningSummary: string;
  languageSummary: string;
  languageNotes: { phrase: string; language: string; meaning: string }[];
  integrity: { type?: string; detail?: string }[];
  perQuestion: { stage: string; question: string; answer: string; score: number | null; note: string }[];
};

type Row = {
  candidate_name: string | null;
  role_title: string;
  status: string;
  overall_score: number | null;
  created_at: string;
  completed_at: string | null;
  report: Json | null;
  answers: Json;
  integrity_events: Json;
};

/** Normalises a stored interview row into the report shown and downloaded on both sides. */
export function toFinalReport(iv: Row): FinalReport {
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const r = (iv.report ?? {}) as Record<string, any>;
  const answers = (iv.answers ?? []) as any[];
  const pq = (r["perQuestion"] ?? []) as any[];
  return {
    name: iv.candidate_name ?? r["name"] ?? "Candidate",
    roleTitle: iv.role_title || r["roleTitle"] || "Scientist B",
    date: new Date(iv.completed_at ?? iv.created_at).toLocaleString(),
    status: iv.status === "completed" ? "Completed" : iv.status === "disqualified" ? "Caught cheating" : "In progress",
    overallScore: iv.overall_score ?? r["overallScore"] ?? null,
    rubric: r["rubric"] ?? [],
    covered: r["covered"] ?? r["coveredConcepts"] ?? [],
    missing: r["missing"] ?? r["missingConcepts"] ?? [],
    reasoningSummary:
      r["reasoningSummary"] ??
      (iv.status === "disqualified" ? "Session terminated after a second integrity violation." : "Evaluation pending."),
    languageSummary: r["languageSummary"] ?? "",
    languageNotes: answers.flatMap((a) => a.languageNotes ?? []),
    integrity: (iv.integrity_events ?? []) as any[],
    perQuestion: answers.map((a, i) => ({
      stage: a.stage ?? "",
      question: a.question ?? "",
      answer: a.text || a.latex || (a.hasDrawing ? "[Handwritten derivation on chalkboard]" : "(not attempted)"),
      score: pq[i]?.score ?? a.score ?? null,
      note: pq[i]?.note ?? a.evaluationNote ?? "",
    })),
  };
}

/** Builds and downloads a clean PDF of the final assessment report. */
export async function downloadReportPdf(rep: FinalReport) {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const M = 48;
  let y = M;
  const navy: [number, number, number] = [11, 37, 69];
  const ensure = (h: number) => {
    if (y + h > H - M) {
      doc.addPage();
      y = M;
    }
  };
  const text = (t: string, size = 10.5, style: "normal" | "bold" | "italic" = "normal", color: [number, number, number] = [26, 26, 26]) => {
    doc.setFont("times", style);
    doc.setFontSize(size);
    doc.setTextColor(...color);
    const clean = t.replace(/[^\x20-\x7E\n]/g, (c) => ({ "—": "-", "–": "-", "“": '"', "”": '"', "’": "'", "‘": "'" })[c] ?? "?");
    const lines = doc.splitTextToSize(clean, W - 2 * M) as string[];
    for (const l of lines) {
      ensure(size * 1.4);
      doc.text(l, M, y);
      y += size * 1.4;
    }
  };
  const heading = (t: string) => {
    y += 10;
    ensure(30);
    text(t.toUpperCase(), 9, "bold", navy);
    doc.setDrawColor(...navy);
    doc.setLineWidth(0.5);
    doc.line(M, y - 6, W - M, y - 6);
    y += 6;
  };

  doc.setFillColor(...navy);
  doc.rect(0, 0, W, 6, "F");
  y = M + 4;
  text("Boardroom AI", 22, "normal", navy);
  text("DRDO Interview Simulation - Final Assessment Report", 10, "normal", [110, 110, 110]);
  y += 8;
  text(`Candidate: ${rep.name}`, 12, "bold");
  text(`Post: ${rep.roleTitle}`);
  text(`Date: ${rep.date}    Status: ${rep.status}`);
  text(`Overall score: ${rep.overallScore ?? "-"} / 100`, 14, "bold", navy);

  if (rep.rubric.length) {
    heading("Rubric");
    rep.rubric.forEach((r) => text(`${r.label}: ${r.score}`));
  }
  heading("How the candidate reasons");
  text(rep.reasoningSummary);
  if (rep.covered.length || rep.missing.length) {
    heading("Concept mapping");
    if (rep.covered.length) text(`Covered: ${rep.covered.join(", ")}`);
    if (rep.missing.length) text(`Missing: ${rep.missing.join(", ")}`);
  }
  heading("Language notes (noted only, never penalised)");
  text(rep.languageSummary || "No non-English usage observed.");
  rep.languageNotes.forEach((n) => text(`"${n.phrase}" - ${n.language}: ${n.meaning}`, 10, "italic"));
  heading("Integrity log");
  if (!rep.integrity.length) text("No integrity events recorded.");
  rep.integrity.forEach((e, i) => text(`${i + 1}. ${e.detail ?? e.type ?? "Event"}`));
  heading("Question-by-question");
  rep.perQuestion.forEach((q, i) => {
    y += 4;
    text(`Q${i + 1} (${q.stage})${q.score !== null ? `  -  score ${q.score}` : ""}`, 10.5, "bold");
    text(q.question);
    text(`Answer: ${q.answer.slice(0, 1500)}`, 10, "italic", [70, 70, 70]);
    if (q.note) text(`Panel note: ${q.note}`, 10);
  });

  doc.save(`Boardroom-AI-Report-${rep.name.replace(/\W+/g, "-")}.pdf`);
}
