# Live architecture and RAG verification

## Scope and result

This note follows the candidate interview path in the current `boardroom-ai` frontend through persistence, question generation, answer evaluation, adaptive progression, and the final scorecard. The live Node-to-Python API path was exercised end to end for radar, aerospace, and cybersecurity roles. Browser sign-in through Google/Supabase and Gemini generation were not available in this workspace and are not claimed as verified.

## Architecture used by the interview screen

1. The authenticated React application resolves the Supabase user profile and advertised role. Supabase remains the identity/profile provider.
2. The application sends the resolved candidate and seeded role identifiers to the Node API through `src/lib/backend-api.ts`.
3. Node creates the durable interview record, snapshots the candidate and role, and calls the Python AI service to start the interview.
4. Python selects the opening question and handles each turn through the orchestrator, adaptive policy, evaluator, and knowledge-base retriever. Node persists the returned question, answer/evaluation, active AI state, retrieval diagnostics, and final report.
5. On completion, Node requests the Python scorecard, stores the full scorecard and report, and returns it to the same React screen for display.

The interview UI no longer creates a static question set or asks a separate browser-side AI function to score a Supabase interview row. The obsolete direct-AI follow-up and finalization functions have been removed. The static question bank is still used by the admin question-bank prototype; it does not drive the candidate interview.

## RAG request path and observed runtime

The live path is `interview.tsx` → `backend-api.ts` → Node `/api/interviews` lifecycle endpoints → Python `/api/interview/start`, `/api/interview/turn`, and `/api/interview/scorecard` → adaptive orchestrator → retriever → question generator/evaluator/scorecard → Node persistence → frontend scorecard.

Python returns per-question retrieval diagnostics. Node stores them with the turn, including whether retrieval ran, retrieved chunk IDs/titles/domains/scores, whether context reached generation, and whether question generation used Gemini or the curated fallback.

Observed during the live API exercise:

- Knowledge base: 84 chunks, including aerospace and cybersecurity material with source attribution.
- Retrieval mode: TF-IDF lexical retrieval. Dense sentence-transformer embeddings were not installed in this workspace.
- Gemini: not configured (`llm_configured: false`); the request therefore used the curated RAG-grounded fallback question path. No claim is made that Gemini generated these questions.
- Radar sample source IDs included `chunk_drdo_fund_dsp_01`, `chunk_drdo_val_02`, and `chunk_drdo_fund_rf_01`, all in `electronics_radar`.
- Aerospace retrieval included `chunk_aero_cfd_01` in `aerospace_aerodynamics`.
- Cybersecurity retrieval included `chunk_cyber_ice_01`, `chunk_cyber_incident_01`, and `chunk_cyber_network_01` in `cyber_computing`.
- Diagnostics confirmed retrieval invocation and retrieved context reaching the generation stage. The fallback question path uses the retrieved material and avoids reusing exhausted curated samples by creating a grounded remediation question.

### RAG status

**RAG PARTIALLY VERIFIED.** A live Node-to-Python request traced actual domain-specific retrieved chunks into the question-generation path. The runtime had no Gemini key, so model-backed Gemini generation was not verified; dense retrieval was also unavailable. Configure the project’s Gemini key and install the optional dense-retrieval dependencies to verify those runtime modes.

## Candidate, role, and storage ownership

- Candidate identity comes from the authenticated Supabase session; candidate records are created or updated by email, so the backend no longer assumes the demo account.
- Seeded role records use stable AI role codes so database-generated IDs do not send the adaptive policy to its generic fallback ladder.
- Node owns interview sessions, turn history, AI state, integrity events, retrieval diagnostics, and scorecards. The frontend reads interview results from Node.
- Supabase remains responsible for authentication and profile resolution. The legacy static admin question-bank prototype remains separate from candidate interview execution.

## Local run outline

Use the project’s `.env.example` to configure Supabase authentication for the frontend, set the frontend API base to the Node API (for example `http://localhost:5000/api`), and set Node’s `AI_SERVICE_URL` to the Python service (for example `http://localhost:8000`). Start the Python service from `ai-service`, start the Node backend from `backend`, run `npm run seed:demo` in the backend, and start the frontend from `boardroom-ai`. Port 5000 was occupied by an unrelated pre-existing process during verification, so this run used Node on port 5001 and frontend API base `http://localhost:5001/api`.

## Verification limits

The end-to-end API exercise used seeded candidate/role records and exercised the actual Node-to-Python interview pipeline. It did not sign in through the real browser OAuth flow because no project Supabase credentials/OAuth setup were supplied. Consequently, the actual browser login, role selection UI, browser Network panel, and browser-rendered scorecard remain to be verified with the project’s configured Supabase/Google OAuth account. The production frontend build verifies compilation, not authenticated browser execution.
