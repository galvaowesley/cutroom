# Fuzzy search over municipality names

| Field | Value |
|---|---|
| Format | deck (PDF, read) |
| Audience | technical |
| Goal | decides whether to use Levenshtein fuzzy search to suggest or to correct municipality names |
| Key message | With up to 3 typos, the search ranks the right municipality first in 85.5% of queries: good for suggesting, not for correcting on its own. |
| Target duration | 17 slides |
| Voice | — |
| Brand | cutroom |

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | municipalities in the IBGE list | 5571 | src/ibge_municipalities.csv | IBGE list of 2026-10-21, seed 2026 |
| F2 | distinct names | 5298 | src/ibge_municipalities.csv | IBGE list of 2026-10-21, seed 2026 |
| F3 | queries generated (0 to 3 errors) | 22284 | src/results.json (from data.py on src/ibge_municipalities.csv) | IBGE list of 2026-10-21, seed 2026 |
| F4 | right name first, 1 to 3 errors | 0.8553705652802303 | src/results.json (from data.py on src/ibge_municipalities.csv), overall.raw.top1 | IBGE list of 2026-10-21, seed 2026 |
| F5 | right name in the top 5, 1 to 3 errors | 0.9494726636921981 | src/results.json (from data.py on src/ibge_municipalities.csv), overall.raw.top5 | IBGE list of 2026-10-21, seed 2026 |
| F6 | exact match, right name first | 0.004316347100925791 | src/results.json (from data.py on src/ibge_municipalities.csv), overall.exact.top1 | IBGE list of 2026-10-21, seed 2026 |
| F7 | right name first with 1 error | 0.95426962594437 | src/results.json (from data.py on src/ibge_municipalities.csv), one_error.raw.top1 | IBGE list of 2026-10-21, seed 2026 |
| F8 | right name first with 3 errors | 0.7476465313862012 | src/results.json (from data.py on src/ibge_municipalities.csv), by_errors.raw.3.top1 | IBGE list of 2026-10-21, seed 2026 |
| F9 | names with an accent | 0.4281098546042003 | src/results.json (from data.py on src/ibge_municipalities.csv), with_accent | IBGE list of 2026-10-21, seed 2026 |
| F10 | names with more than one word | 0.4781906300484653 | src/results.json (from data.py on src/ibge_municipalities.csv), compound | IBGE list of 2026-10-21, seed 2026 |
| F11 | first place in the Sudeste | 0.8419113869327671 | src/results.json (from data.py on src/ibge_municipalities.csv), by_region | IBGE list of 2026-10-21, seed 2026 |
| F12 | first place in the Sul | 0.8771921772713764 | src/results.json (from data.py on src/ibge_municipalities.csv), by_region | IBGE list of 2026-10-21, seed 2026 |
| F13 | share of queries, names up to 6 letters | 0.13893376413570274 | src/results.json (from data.py on src/ibge_municipalities.csv), length[0] | IBGE list of 2026-10-21, seed 2026 |
| F14 | share of misses, names up to 6 letters | 0.4008686528846419 | src/results.json (from data.py on src/ibge_municipalities.csv), length[0] | IBGE list of 2026-10-21, seed 2026 |
| F15 | first place, 3 errors, names up to 6 letters | 0.35090070568851794 | src/results.json (from data.py on src/ibge_municipalities.csv), heat | IBGE list of 2026-10-21, seed 2026 |
| F16 | misses with 1 swap (transposition) | 0.1270420842939927 | src/results.json (from data.py on src/ibge_municipalities.csv), by_kind | IBGE list of 2026-10-21, seed 2026 |
| F17 | swap misses / deletion misses | 2.5076757279360415 | src/results.json (from data.py on src/ibge_municipalities.csv), by_kind | IBGE list of 2026-10-21, seed 2026 |
| F18 | right name first, accents removed | 0.8503922030055476 | src/results.json (from data.py on src/ibge_municipalities.csv), overall.folded.top1 | IBGE list of 2026-10-21, seed 2026 |
| F19 | size of the suggestion list | 5 names | definition: top-5 in src/data.py, measure() | — |
| F20 | upper bound of the shortest length band | 6 letters | definition: bands in src/data.py, main() | — |

## Scenes

### 1. cutroom-deck example · slide 1

- **Goal:** name the piece and its key message.
- **On screen:** Fuzzy search over municipality names
- **Speech:** —
- **Visual:** cutroom-deck: deck.cover.
- **Facts:** F1, F3

### 2. Summary · slide 2

- **Goal:** give the verdict and the three numbers before any detail.
- **On screen:** With up to 3 typos, the search ranks the right municipality first in 85.5% of queries
- **Speech:** —
- **Visual:** cutroom-deck: ui.summary.
- **Facts:** F4, F5, F6, F7

### 3. How we measured · slide 3

- **Goal:** show how the queries were built and checked.
- **On screen:** We built queries with typos from the official list and checked where the right name lands in the queue
- **Speech:** —
- **Visual:** cutroom-deck: ill.timeline + ui.steps.
- **Facts:** F1, F2, F3

### 4. What distance is · slide 4

- **Goal:** explain edit distance with two real queries.
- **On screen:** Distance counts the edits from the query to the name, and the search ranks names by it
- **Speech:** —
- **Visual:** cutroom-deck: ill.waterfall of two real queries.
- **Facts:** —

### 5. What ranking is · slide 5

- **Goal:** explain ranking and why first place is what people see.
- **On screen:** For whoever searches, what matters is the right name being first in the candidate queue
- **Speech:** —
- **Visual:** cutroom-deck: ill.queue_scenarios.
- **Facts:** —

### 6. The three measures · slide 6

- **Goal:** define the three measures.
- **On screen:** Three numbers sum up the search: first place, the top 5, and the ranking of the whole queue
- **Speech:** —
- **Visual:** cutroom-deck: ui.measures.
- **Facts:** F4, F5, F19

### 7. Typing errors · slide 7

- **Goal:** show how each extra error lowers the rate.
- **On screen:** Each extra error lowers first-place hits: from 95.4% with 1 error to 74.8% with 3
- **Speech:** —
- **Visual:** cutroom-deck: ill.small_multiples.
- **Facts:** F7, F8

### 8. Which names · slide 8

- **Goal:** show which names the base has.
- **On screen:** 43% of the names have an accent and 48% have more than one word
- **Speech:** —
- **Visual:** cutroom-deck: ill.composition + ill.availability.
- **Facts:** F9, F10

### 9. By region · slide 9

- **Goal:** compare regions with intervals.
- **On screen:** First-place hits go from 84.2% in the Sudeste to 87.7% in the Sul
- **Speech:** —
- **Visual:** cutroom-deck: ill.segment_table.
- **Facts:** F11, F12

### 10. Name length · slide 10

- **Goal:** show where misses concentrate.
- **On screen:** Names of up to 6 letters are 14% of queries and 40% of the misses
- **Speech:** —
- **Visual:** cutroom-deck: ill.paired_bars + ill.concentration_bars.
- **Facts:** F13, F14, F20

### 11. Length × errors · slide 11

- **Goal:** cross name length with the number of errors.
- **On screen:** With 3 errors, names of up to 6 letters come first in 35% of queries
- **Speech:** —
- **Visual:** cutroom-deck: ill.heatmap + ill.lines.
- **Facts:** F15, F20

### 12. Error kinds · slide 12

- **Goal:** rank the error kinds.
- **On screen:** With 1 error, a swap pushes the right name out of first place in 12.7% of queries, 2.5x a deletion
- **Speech:** —
- **Visual:** cutroom-deck: ill.weights.
- **Facts:** F16, F17

### 13. Removing accents · slide 13

- **Goal:** explain why removing accents did not help.
- **On screen:** Removing accents fixes accent errors but raises misses for the other kinds: 85.0% against 85.5% overall
- **Speech:** —
- **Visual:** cutroom-deck: ill.paired_bars.
- **Facts:** F18, F4

### 14. Verdict · slide 14

- **Goal:** state strengths and limits.
- **On screen:** Strengths and limits
- **Speech:** —
- **Visual:** cutroom-deck: ui.strengths_limits.
- **Facts:** F4, F6

### 15. How to use it today · slide 15

- **Goal:** say how to use it today.
- **On screen:** Use the search to suggest a list of names, not to correct the query on its own
- **Speech:** —
- **Visual:** cutroom-deck: ui.use_for + ill.grid.
- **Facts:** F5

### 16. Next steps · slide 16

- **Goal:** propose next steps with conditions.
- **On screen:** Proposed next steps
- **Speech:** —
- **Visual:** cutroom-deck: ui.proposals.
- **Facts:** F16

### 17. Close · slide 17

- **Goal:** close with where the code and data are.
- **On screen:** Fuzzy search over municipality names
- **Speech:** —
- **Visual:** cutroom-deck: deck.closing.
- **Facts:** —

## Pronunciation

| written | spoken |
|---|---|
