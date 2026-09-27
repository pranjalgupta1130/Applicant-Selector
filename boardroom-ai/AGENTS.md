<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

# Boardroom AI — architecture rules

- Auth is Google via Lovable Cloud; `/auth` is the only sign-in page and routes by role after `ensure_profile()`. Why: single entry point, profile + default candidate role created once.
- Roles live in `public.user_roles` (`admin` | `candidate`), checked with `has_role()`. Admin granted only by `claimAdmin` server fn matching the `ADMIN_INVITE_CODE` secret. Why: prevents privilege escalation.
- Candidate pages live under `src/routes/_authenticated/`; staff pages under `src/routes/_authenticated/_admin/` (role gate in its `route.tsx`). Why: role separation enforced before render.
- Interviews persist in `public.interviews` (answers, integrity_events, report jsonb); candidates update only while `in_progress`. Why: sealed after completion/disqualification.
- AI (follow-ups, language notes, final evaluation) runs server-side in `src/lib/interview.functions.ts` via `ai.server.ts` (Lovable AI, openai/gpt-6-astra, Responses API). Why: keys stay on server.
- Proctoring is client-side in `src/hooks/useProctor.ts` (MediaPipe face landmarker loaded dynamically + browser signals); 1 warning then termination. Why: no video leaves the device.
- Voice answers use browser speech recognition; question narration uses speech synthesis (`en-IN`, 0.75×/1×/1.25×) and cancels between questions. Why: accessible, keyless speech.
- Language notes combine AI analysis with a deduplicated Indian-language glossary. Why: Roman-script regional terms remain detectable if AI analysis fails.
- Motion handles reveals/doors; Anime.js sequences entrance/logo details; reduced motion is respected. Why: polished public motion without interview distraction.
