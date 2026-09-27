import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";

/** Grants the admin role when the DRDO staff invite code matches. */
export const claimAdmin = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ code: z.string().min(1).max(100) }).parse(d))
  .handler(async ({ data, context }) => {
    // "1234" is the dummy staff passcode for demos; the configured secret also works.
    const valid = [process.env["ADMIN_INVITE_CODE"], "1234"].filter(Boolean);
    if (!valid.includes(data.code.trim())) {
      return { ok: false as const, message: "That staff invite code is not valid." };
    }
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error: grantError } = await supabaseAdmin
      .from("user_roles")
      .upsert({ user_id: context.userId, role: "admin" }, { onConflict: "user_id,role" });
    if (grantError) throw new Error("Panel access could not be granted.");
    const { error: cleanupError } = await supabaseAdmin
      .from("user_roles")
      .delete()
      .eq("user_id", context.userId)
      .eq("role", "candidate");
    if (cleanupError) throw new Error("Panel access could not be completed.");
    return { ok: true as const };
  });

export type LanguageNote = { phrase: string; language: string; meaning: string };

const REGIONAL_TERMS: Array<LanguageNote & { pattern: RegExp }> = [
  { phrase: "achha", language: "Hindi/Hinglish", meaning: "okay / I see", pattern: /\b(?:achha|accha|acha)\b/gi },
  { phrase: "haan", language: "Hindi/Hinglish", meaning: "yes", pattern: /\b(?:haan|hanji)\b/gi },
  { phrase: "matlab", language: "Hindi/Hinglish", meaning: "meaning / that is", pattern: /\bmatlab\b/gi },
  { phrase: "theek hai", language: "Hindi/Hinglish", meaning: "it is okay", pattern: /\btheek\s+hai\b/gi },
  { phrase: "thoda", language: "Hindi/Hinglish", meaning: "a little", pattern: /\bthod[ai]\b/gi },
  { phrase: "jugaad", language: "Hindi/Hinglish", meaning: "an improvised practical solution", pattern: /\bjugaad\b/gi },
  { phrase: "dhanyavaad", language: "Hindi", meaning: "thank you", pattern: /\bdhanyavaad\b/gi },
  { phrase: "mala", language: "Marathi", meaning: "to me / I", pattern: /\bmala\b/gi },
  { phrase: "majha", language: "Marathi", meaning: "my", pattern: /\bmajh[ae]\b/gi },
  { phrase: "changla", language: "Marathi", meaning: "good", pattern: /\bchangl[ae]\b/gi },
  { phrase: "aahe", language: "Marathi", meaning: "is", pattern: /\baahe\b/gi },
  { phrase: "vanakkam", language: "Tamil", meaning: "greetings", pattern: /\bvanakkam\b/gi },
  { phrase: "nandri", language: "Tamil", meaning: "thank you", pattern: /\bnandri\b/gi },
  { phrase: "namaskaram", language: "Telugu/Malayalam", meaning: "greetings", pattern: /\bnamaskaram\b/gi },
  { phrase: "dhanyavadalu", language: "Telugu", meaning: "thank you", pattern: /\bdhanyavadalu\b/gi },
  { phrase: "dhonnobad", language: "Bengali", meaning: "thank you", pattern: /\b(?:dhonnobad|dhanyabad)\b/gi },
];

function detectRegionalTerms(answer: string): LanguageNote[] {
  return REGIONAL_TERMS.flatMap(({ pattern, language, meaning }) => {
    const matches = answer.match(pattern) ?? [];
    return matches.map((phrase) => ({ phrase, language, meaning }));
  });
}

function mergeLanguageNotes(...groups: LanguageNote[][]): LanguageNote[] {
  const seen = new Set<string>();
  return groups.flat().filter((note) => {
    const key = `${note.phrase.trim().toLocaleLowerCase()}|${note.language.toLocaleLowerCase()}`;
    if (!note.phrase.trim() || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** Smart follow-up + language analysis of the candidate's last answer. */
export const followUp = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) =>
    z
      .object({
        roleTitle: z.string().max(200),
        question: z.string().max(2000),
        answer: z.string().max(8000),
        history: z.array(z.string().max(1000)).max(6),
        wantFollowUp: z.boolean(),
        spoken: z.boolean(),
      })
      .parse(d),
  )
  .handler(async ({ data }) => {
    const { aiJson } = await import("./ai.server");
    const glossaryNotes = detectRegionalTerms(data.answer);
    try {
      const result = await aiJson<{ followUp: string | null; languageNotes: LanguageNote[]; kind: "derivation" | "reasoning" }>(
        `You are a senior DRDO selection-board panellist interviewing for ${data.roleTitle}.
Given the question and the candidate's answer, ${
          data.wantFollowUp
            ? "write ONE short and easy follow-up question (maximum 18 words) about exactly what the candidate said. Ask for a simple example or one basic clarification. Never introduce an advanced concept and never repeat earlier follow-ups. If the answer is empty, ask a very simple scaffolding question on the same topic."
            : "set followUp to null."
        }
Also set "kind": "derivation" if the follow-up needs maths/diagrams, else "reasoning".
Inspect the transcript word by word. List every non-English word or short phrase separately, including Roman-script Hinglish, Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Punjabi, Kannada, Malayalam, Urdu, and foreign-language words. Do not combine different terms into one note. Preserve the exact spoken spelling in "phrase", identify the most likely language, and give a brief English meaning. Also detect code-switching discourse words such as achha, haan, matlab, theek hai, thoda, mala, majha, aahe, vanakkam, nandri, namaskaram, and dhonnobad. Do not label ordinary Indian English pronunciation as a foreign word. Empty array only when no such term appears. These notes are neutral and must never affect scoring.
JSON shape: {"followUp": string|null, "kind": "derivation"|"reasoning", "languageNotes": [...]}`,
        `Question: ${data.question}\nEarlier follow-ups: ${data.history.join(" | ") || "none"}\nAnswer (${
          data.spoken ? "voice transcript" : "typed/latex"
        }): ${data.answer || "(no answer)"}`,
      );
      return { ...result, languageNotes: mergeLanguageNotes(glossaryNotes, result.languageNotes ?? []) };
    } catch (e) {
      console.error(e);
      return { followUp: null, kind: "reasoning" as const, languageNotes: glossaryNotes, error: true };
    }
  });

/** Evaluates a completed interview and stores the report. */
export const finalizeInterview = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ interviewId: z.string().uuid() }).parse(d))
  .handler(async ({ data, context }) => {
    const { data: row, error } = await context.supabase
      .from("interviews")
      .select("*")
      .eq("id", data.interviewId)
      .eq("candidate_id", context.userId)
      .single();
    if (error || !row) throw new Error("Interview not found");
    if (row.status !== "in_progress") return { ok: true };

    const answers = (row.answers as Array<Record<string, unknown>>).map((a) => ({
      question: a["question"],
      stage: a["stage"],
      isFollowUp: a["isFollowUp"],
      answer: a["text"] || a["latex"] || (a["hasDrawing"] ? "[handwritten derivation on chalkboard]" : "(not attempted)"),
      languageNotes: a["languageNotes"],
    }));
    const { aiJson } = await import("./ai.server");
    let report: Record<string, unknown>;
    try {
      report = await aiJson<Record<string, unknown>>(
        `You are the DRDO selection board chair writing the evaluation for ${row.role_title}. The interview intentionally uses elementary questions, so assess clarity and basic understanding without expecting advanced derivations.
Score 0-100. JSON shape: {"overallScore": number, "rubric": [{"label":"Relevance"|"Technical Correctness"|"Completeness"|"Reasoning"|"Clarity","score":number}],
"coveredConcepts": string[], "missingConcepts": string[], "reasoningSummary": string (4-6 sentences, how they think),
"languageSummary": string (neutral note on any Hinglish/regional language use, or "No non-English usage observed."),
"perQuestion": [{"question": string, "stage": string, "score": number, "note": string}]}
Keep each coveredConcepts and missingConcepts entry concise: maximum six words. Never penalise language mixing; only note it. Handwritten answers cannot be read — score them as partially evidenced.`,
        JSON.stringify(answers).slice(0, 30000),
      );
    } catch (e) {
      console.error(e);
      report = { overallScore: null, reasoningSummary: "Automatic evaluation unavailable; panel to review manually.", rubric: [], coveredConcepts: [], missingConcepts: [], perQuestion: [], languageSummary: "" };
    }
    await context.supabase
      .from("interviews")
      .update({
        status: "completed",
        report: report as never,
        overall_score: typeof report["overallScore"] === "number" ? Math.round(report["overallScore"] as number) : null,
        completed_at: new Date().toISOString(),
      })
      .eq("id", data.interviewId);
    return { ok: true };
  });
