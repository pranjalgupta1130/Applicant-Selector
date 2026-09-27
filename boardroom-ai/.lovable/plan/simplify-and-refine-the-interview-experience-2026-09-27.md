# Simplify and refine the interview experience

## What will change
- Replace the current technical bank with four easy questions per interview: one icebreaker, one simple role question with two easy follow-ups, one basic theory question, and one short numerical.
- Add a read-aloud control beside every question with 0.75×, 1×, and 1.25× speeds, using the browser voice and stopping cleanly between questions.
- Strengthen language analysis so each Hindi, Hinglish, Marathi, Tamil, Telugu, Bengali, and other non-English term is returned as a separate note with language and meaning; keep it neutral and never penalise it.
- Make the assessment's “concepts engaged / not reached” text smaller, cleaner, and easier to scan instead of long oversized pills.
- Replace the sign-in slogan with a verified set of attributed quotes from notable Indian scientists, choosing a different quote for each fresh sign-in visit.
- Remove the three-column landing strip so the boardroom image, message, and entry action fit in the first screen without scrolling.

## Simple question-and-answer set
1. **Icebreaker:** Tell us about yourself and why you want to work in research and development.
   **Sample answer:** I am an engineering graduate who enjoys solving practical problems. I want to work in research and development because it lets me apply technical knowledge to systems that can help the country.

2. **Simple technical question:** What is the difference between speed and velocity?
   **Sample answer:** Speed tells us how fast an object moves. Velocity tells us both how fast it moves and its direction.
   **Follow-up 1:** Can speed stay constant while velocity changes?
   **Answer:** Yes. In circular motion, speed can stay constant while direction changes, so velocity changes.
   **Follow-up 2:** Give one everyday example.
   **Answer:** A car moving around a roundabout at a steady speed has changing velocity because its direction keeps changing.

3. **Theory question:** What is the difference between accuracy and precision?
   **Sample answer:** Accuracy means being close to the correct value. Precision means getting nearly the same result repeatedly. Measurements can be precise but still inaccurate if the instrument is poorly calibrated.

4. **Numerical question:** A 2 kg object moves at 3 m/s. Find its kinetic energy.
   **Sample answer:** Kinetic energy = ½mv² = ½ × 2 × 3² = 9 joules.

## Technical details
- Keep the existing four-question, single-pass interview flow and two-follow-up structure.
- Use the browser Speech Synthesis API for read-aloud; no new external service or key.
- Tighten the AI prompt and add deterministic transcript token separation before saving language notes.
- Preserve the current professional forest-and-brass design and existing motion accessibility settings.
