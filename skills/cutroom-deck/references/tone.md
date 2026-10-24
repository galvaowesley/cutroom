# Deck tone

The general tone rules are in `references/tone.md` of the `cutroom-script` skill, always installed in the same skill
folder, and the brand's own voice in its `VOICE.md`. Below, what applies to slides in particular.

## Sober and scientific

- Describe what was measured and compare it with a reference: chance, an agreed criterion, the previous period, a
  simple method.
  - Good: "finds the right match 85.5% of the time; exact matching finds it 0.4%".
  - Bad: "finds it very often".
- When claiming a difference, show the confidence interval (`fmt.wilson`, `ill.segment_table`) and say whether the
  intervals overlap.
- No superlatives ("very", "strong", "the biggest", "the best") and no alarm words ("critical", "worrying"). Use the
  numeric comparison: "2.5x the deletions", "from 84.2% to 87.7%".
- Titles are factual sentences with the number. Not slogans, not questions.

## Only what was verified

- Separate fact from hypothesis. A hypothesis goes on a card with the kicker "Hypothesis", with the evidence for and
  against, and what was not measured.
- Before claiming an effect on a product or on people, check where the data comes from. If you could not, say so on
  the slide or remove the claim.
- Fictitious illustrations carry the label. Real examples carry the source.

## Numbers

- **Every number comes from the data**, including those inside sentences and ratios ("1 in 7", "2.9x").
- **Add before rounding**, format only at the end: 0.0726 + 0.0218 gives 9.4%, not 7.3% + 2.2% = 9.5%.
- **Locale:** the deck's `lang` sets the format: `fmt.pct(0.855)` gives "85.5%" in English and "85,5%" in
  Portuguese; `fmt.num(5571)` "5,571" or "5.571"; `fmt.mult(2.31)` "2.3x"; `fmt.size(1_536_000)` "1.5 MB";
  `fmt.duration(64)` "1 min 4 s".
- **Keep the source's decimals:** if the source says "14.0 s" or "22.42 s", so does the slide. Do not round for the
  sake of it, and do not change units (0.8 GB does not become "800.0 MB").
- **Executive:** percentages, not absolutes. **Technical:** both, with the sample size.
- **"k out of 100":** round k to an integer and keep the exact percentage next to it (`ill.grid(100 * rate)` +
  `fmt.pct(rate)`).

## Next steps and verdict

- Next steps are proposals ("evaluate", "test", "review"), each with its adoption condition ("adding it depends on
  the gain being confirmed on the same queries"). No dates, no promised results.
- The verdict fits one line and says what the thing is for and what it is not for, with the number that justifies it.

## Recurring decks

Titles and conclusion sentences can come from the data through simple rules (e.g. "above/below the criterion").
Review each against the edition's number before circulating.
