# Integration fix report

## Previously reported issues

| Symptom | Root cause | Fix | Main files | Verification |
|---|---|---|---|---|
| Candidate accounts other than the demo account could fail with a 404 during login/application. | The frontend and backend had separate identity/persistence assumptions; backend candidate creation did not update an existing candidate by email. | Candidate lookup/upsert now supports existing and new authenticated candidate profiles; application resolves the advertised backend role and stores backend IDs for the interview. | `backend/src/services/candidate.service.js`, `backend/src/models/Candidate.js`, `boardroom-ai/src/routes/_authenticated/apply.tsx`, `boardroom-ai/src/lib/backend-api.ts` | Backend API flow exercised with seeded candidates and multiple role profiles. Real Supabase/Google browser login was not available to test in this environment. |
| Questions were static or fell back to the same generic question ladder across roles. | The live interview screen generated a local static question set and bypassed Python. Separately, adaptive policy used generated database IDs as role identifiers and could not select advertised-domain question ladders. | Candidate interview now starts and advances through Node→Python. Stable role AI codes, role-specific competency ladders, candidate-skill routing, domain knowledge chunks, retrieval diagnostics, and grounded remediation questions were added. | `boardroom-ai/src/routes/_authenticated/interview.tsx`, `ai-service/adaptive/policy.py`, `ai-service/adaptive/orchestrator.py`, `ai-service/core/concepts.py`, `ai-service/generator/pipeline.py`, `backend/src/seed/seed-demo.js`, `data/knowledge_base/seed_knowledge.json` | Live API flows retrieved domain-specific sources for radar, aerospace, and cyber. Python regression suite passed. Gemini itself was unconfigured, so observed generation used the curated RAG-grounded fallback. |
| Final evaluation was missing from the completed interview. | The frontend finalized a separate Supabase row through a browser-side AI function rather than requesting the Python scorecard and reading the result from the same interview service. | Node now requests the Python evidence-based scorecard, persists it with the report and completed interview, and returns the scorecard for immediate display in the interview UI. Legacy direct-AI `followUp` and `finalizeInterview` paths were removed. | `backend/src/services/closed-loop-interview.service.js`, `backend/src/controllers/interview.controller.js`, `backend/src/models/Interview.js`, `backend/src/models/Report.js`, `boardroom-ai/src/routes/_authenticated/interview.tsx`, `boardroom-ai/src/lib/interview.functions.ts` | Live API sessions returned completed scorecards; strong and off-topic aerospace answer sets scored 96 and 0 respectively after competency profiles were added. |

## Architecture now used

Candidate UI → Node interview API → Python interview start/turn/scorecard APIs → adaptive policy, retrieval, generation, evaluation, and scorecard → Node persistence → candidate UI.

Supabase is used for authentication/profile identity. Node stores interview state and reports. The admin static question bank remains a prototype tool and is not used for a candidate interview.

## Test and live-run results

- Python suite: **246 passed, 4 skipped**, one upstream Starlette/httpx deprecation warning.
- Frontend production build: successful.
- Node source syntax checks: successful.
- Live Node→Python API results: radar completed at **89**; cybersecurity at **98**; aerospace strong-answer run at **96**; aerospace off-topic-answer run at **0**. Each response included a completed status and scorecard; strong evidence scored above off-topic evidence.
- Retrieval diagnostics: role/domain-specific source chunks were returned for radar, aerospace, and cybersecurity, with retrieval invoked and context passed to question generation.

## Runtime limitations and remaining checks

1. No Gemini API key was configured. The verified question-generation mode was the curated, retrieved-context fallback. To verify Gemini question generation, run the app with a configured Gemini key and inspect stored per-turn diagnostics (`generationMode`, source IDs, retrieval mode, and context flag).
2. Dense embeddings were unavailable; the live retriever used TF-IDF lexical search over 84 knowledge chunks.
3. No Supabase project credentials or Google OAuth setup were supplied. The browser login/application flow and browser Network trace were not exercised. Configure the project’s frontend Supabase URL/key and Google provider before claiming authenticated browser E2E is complete.
4. Port 5000 was occupied by another process during validation; the test Node server ran on port 5001. The frontend API base must match the chosen Node port.
