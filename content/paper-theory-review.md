# Paper-theory expansion review

September 20, 2026. Scope: SWA bounded replay, Single-Pass mHC, DSpark, task construction, and sidebar lesson search.

- Source: pinned DeepSeek-V4.1-Flash report sections 2.4.1, 2.4.3, 3.2.1–2, 5.1.1; per-lesson source ledgers record distinctions.
- Corrected SWA exact replay to cap at available prefix length: min(8, 4×3)=8, separately showing the theoretical span12.
- Corrected mHC timing so the residual update waits for the block output; A shifts, B/C do not.
- Replaced opaque DSpark score with expected accepted draft tokens Σ prefix-survival / explicitly invented cost. Default L3, expected2.312512, cost2.35; excludes correction/bonus tokens.
- Browser: replay stage works, shifted mHC next step works, DSpark confidence slider changes expected count, training-task shortcut passes2/3 stronger checks and correct version3/3. Earlier weak-check test accepted all three candidates as designed.
- Sidebar query draft finds exactly the new DSpark lesson; clearing restores navigation.
- Browser at442px: document width442, no overflowing descendants in four new lessons; inspected mHC and DSpark screenshots. No captured browser warnings/errors.
- Build source/generated parity and saved editable-ID validation passed. Four Python build tests and Engram lab regression checks passed; JS syntax checks passed.
- No new model evaluation, measured speedup, training job, narration, or video generated. All widgets are labeled illustrative.

## Navigation and ending revision

Eight collapsible chapters, 24 lesson links and 89 editable-heading step links. All113 targets resolve in the browser. Nested search reveals the confidence subsection; direct clicking updates the URL and lands on its heading without expanding all intermediate chapters. Expand/collapse controls and mobile Escape close verified. Current step uses aria-current. Desktop sidebar300px, main content starts300px; no horizontal document overflow at tested desktop or442px widths. Mobile author toolbar bottom and sidebar top both104px, preventing overlap. Temporary desktop viewport override reset. Ending has review cards, existing-lab links, self-check, and explicitly upcoming topics.

## Architecture unit examples

Added projection after CED explanation, gather between indexer-selection and attention combination, and two-stream mixing before mHC scheduling. Invented scalar/vector examples, not actual V4.1 activations. All six Python assertions passed; all six corresponding browser checks passed. Empty, wrong, and correct answer feedback verified. All three step links appear in contents. At442px document width442; projection screenshot visually inspected; no captured console errors.
