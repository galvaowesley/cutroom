# Tone

Applies to **On screen:**, **Speech:**, the key message and any text of the piece. `cutroom script check` catches
part of this (superlatives, numbers without facts, long titles). The rest is your review. The brand's `VOICE.md`
(`cutroom brand show --json` → `paths.voice_md`) adds the brand's own voice on top of these rules.

## Sober and scientific

- Describe what was measured and compare it with a reference: chance, an agreed criterion, the previous period, a
  control group. A number without a reference does not say whether the result is good or bad.
- When claiming a difference ("rose", "is higher", "improved"), give the confidence interval (95% CI) or say the
  difference is within noise. Without a CI, describe: "went from 12% to 15%", not "improved".
- Example: "The rate went from 12% to 15% compared with August (95% CI of the difference: 1 to 5 points)."

## No superlatives, no alarm

Out: very, extremely, huge, incredible, amazing, revolutionary, game-changing, the best, the biggest, drastic,
dramatic, critical, alarming, shocking, massive, unprecedented. The number gives the weight:

| Instead of | Write |
|---|---|
| a huge increase | an increase of 2.3 times compared with July |
| a drastic drop | a drop of 18% compared with the previous quarter |
| a critical problem | affects 4% of orders |
| the best model | the model with the highest AUC of the three tested (0.71) |

"Strengths", as a heading of the verdict, does not count.

## Next steps are proposals

- Use proposal verbs (evaluate, test, review, compare) and state the adoption condition: "test the new filter;
  adoption depends on the gain repeating in a second window".
- No dates and no promised results: no "by December", no "will cut 20%".

## Only what was verified

- A fact is what has a row in the facts table, with a source. A hypothesis appears as one ("one possible
  explanation", "not yet verified") and never becomes a title.
- Before claiming an effect on a product or its users, check where the product reads the data. If you could not
  check, remove the claim or say it was not verified.
- An illustrative number is marked in the piece itself.

## Add before rounding

- Add raw values and only then format: 0.0726 + 0.0218 = 0.0944, or 9.4%; not 7.3% + 2.2% = 9.5%. In the facts
  table, the value is the unrounded total. The screen shows the rounded one.
- Parts that should add up to 100% and give 99% or 101% after rounding: say "the sum differs from 100% because of
  rounding".

## By audience

- **Executive:** few metrics, each with a plain name defined the first time it appears ("p95 latency" becomes "the
  time in which 95 of every 100 requests finish"). Verdict and decision before method. No code-level
  recommendations. Simple, but never childish.
- **Technical:** the technical name, the method, the sample size, the limits and the technical recommendations.

## Speech

- Spell out numbers and acronyms when the reading is ambiguous: "$1.2M" becomes "one point two million dollars",
  "9.4%" becomes "nine point four percent". Put the same number in digits **On screen:**, where `check` verifies it.
- Short sentences, one idea each. Punctuation becomes pause: comma short, full stop long.
- Foreign names, versions and acronyms the voice reads badly go to the pronunciation table, not into the speech:
  captions keep the spelling. Check how the voice reads them first (`voice test narrator "ManimGX 0.1.1"`).
- At most ~25 s of speech per scene with Kokoro (`references/arcs.md`).
- Read it aloud. Where you stumble, rewrite.

## Review

- [ ] The key message fits one sentence and appears at the start and at the close.
- [ ] Every number on screen and in speech has a fact with source and period.
- [ ] Every claimed difference has a reference, and a CI when the claim asks for one.
- [ ] No superlatives, no alarm; next steps are proposals with an adoption condition.
- [ ] Hypotheses appear as hypotheses.
- [ ] Sums were made before rounding.
- [ ] The speech, read aloud, does not stumble, and the acronyms are in the pronunciation table.
- [ ] The text follows the brand's `VOICE.md`.
