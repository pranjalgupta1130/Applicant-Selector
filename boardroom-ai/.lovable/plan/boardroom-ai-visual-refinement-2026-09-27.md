# Boardroom AI visual refinement

## What will change
- Remove the entire Premium section from the candidate dashboard, including its upgrade action and related wording.
- Remove the “How it works” button from the landing page while keeping the useful feature overview below the opening section.
- Replace the current letter tile with a new Boardroom AI logo combining a selection panel/table motif with an interview board, then use it consistently in the header and sign-in page.
- Refine the landing, sign-in, and candidate dashboard presentation so it feels editorial and deliberately designed rather than template-like: stronger hierarchy, restrained navy/emerald accents, cleaner spacing, subtle texture, and fewer decorative cards.
- Add purposeful interaction without distracting interview candidates: Motion for page/section entrances and responsive controls, and Anime.js for a restrained logo/board-line sequence on public-facing screens.

## Interaction principles
- Keep motion short, calm, and professional.
- Respect reduced-motion preferences.
- Do not animate the timed interview in ways that distract from answering or affect layout.
- Preserve the existing light-only boardroom identity, role-based access, reports, and interview behavior.

## Technical details
- Add the official `motion` and `animejs` React-compatible packages.
- Create small reusable motion wrappers rather than scattering animation logic across pages.
- Generate the logo as a reusable transparent image asset and verify it remains readable at header size.
- Update page metadata copy that still mentions Premium.
- Check desktop and mobile layouts, page interactions, and the current build status after the changes.
