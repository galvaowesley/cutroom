"""Deck: evaluating fuzzy search over Brazilian municipality names (cutroom-deck example).

Every number comes from results.json (written by data.py from IBGE's official list). No value is typed by hand.
Build it in another brand with `deck build <folder> --brand paper`.
"""
import json
from pathlib import Path

from cutroom_deck import Deck, fmt, ill, ui
from cutroom_deck.fmt import dec, num, pct

R = json.loads((Path(__file__).with_name("results.json")).read_text(encoding="utf-8"))
G, U, X, N = R["overall"]["raw"], R["one_error"]["raw"], R["overall"]["exact"], R["overall"]["folded"]
BY_E = R["by_errors"]["raw"]
NEG = R["distinct_names"] - 1
SHORT = R["length"][0]
MISS_MEAN = R["miss_raw_mean"]
KINDS = R["by_kind"]
REG = R["by_region"]
cap = lambda s: s[0].upper() + s[1:]  # noqa: E731
nth = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"  # noqa: E731

deck = Deck("Fuzzy search over municipality names", footer="Fuzzy search over municipality names · October 2026 evaluation",
            slug="fuzzy-search-municipalities", lang="en")
t = deck.theme

SOURCE = (f"IBGE list of municipalities (localities API), downloaded {fmt.date(R['downloaded'])}: "
          f"{num(R['municipalities'])} municipalities, {num(R['distinct_names'])} distinct names.")
SOURCE_ERR = f"{SOURCE} {num(R['queries'] * 3 // 4)} queries with 1 to 3 errors, lowercase text."

# 1. Cover
deck.cover("cutroom-deck example", "Fuzzy search over municipality names",
           "How often Levenshtein distance finds the right town despite typos",
           f"{num(R['municipalities'])} IBGE municipalities and {num(R['queries'])} queries measured in {fmt.month_long(R['downloaded'])}")

# 2. Summary
deck.slide("Summary", f"With up to 3 typos, the search ranks the right municipality first in {pct(G['top1'])} of queries",
           ui.summary("Good for suggesting, not for correcting on its own",
                      f"The right name is first in {pct(G['top1'])} of queries with 1 to 3 errors and in the top 5 in "
                      f"{pct(G['top5'])}. Exact text matching gets {pct(X['top1'])}.",
                      [("Right name first", pct(G["top1"]), f"exact match: {pct(X['top1'])}"),
                       ("In the top 5", pct(G["top5"]), "in a list of 5 suggestions"),
                       ("With 1 error", pct(U["top1"]), "right name first")],
                      [f"<b>Removing accents</b> before comparing fixes accent errors ({pct(KINDS['accent']['miss_raw'])} → "
                       f"{pct(KINDS['accent']['miss_folded'])} misses), but the total drops to {pct(N['top1'])} from {pct(G['top1'])}.",
                       f"<b>Swapping</b> two neighboring letters pushes the right name out of first place in "
                       f"{pct(KINDS['transposition']['miss_raw'])} of 1-error queries.",
                       f"<b>Names of up to 6 letters</b> are {pct(SHORT['pct_queries'], 0)} of queries and "
                       f"{pct(SHORT['pct_misses'], 0)} of the misses."]),
           source=SOURCE_ERR)

# 3. How we measured
deck.slide("How we measured", "We built queries with typos from the official list and checked where the right name lands in the queue",
           ill.timeline(["official list", "query with typos", "candidate queue", "check"],
                        milestones=[(0, "1", True), (1, "2", False), (2, "3", False), (3, "4", True)],
                        span=(1, 3, "one query: from typed text to first place"), h=170),
           ui.steps([("database", "Official list", f"{num(R['municipalities'])} IBGE municipalities, {num(R['distinct_names'])} distinct names."),
                     ("text", "Queries with typos", f"Each name gets 0, 1, 2 and 3 random errors (accent, missing, extra, wrong or swapped letter): {num(R['queries'])} queries."),
                     ("search", "Candidate queue", f"The {num(R['distinct_names'])} names are ranked by distance to the query, nearest first."),
                     ("check", "Check", "Is the right name first? In the top 5? The next pages measure that.")]),
           source=f"{SOURCE} Errors drawn with a fixed seed ({R['seed']}), so the result is reproducible.")

# 4. Concept: edit distance
ex, tr = R["example"], R["example_transposition"]
deck.slide("What distance is", "Distance counts the edits from the query to the name, and the search ranks names by it",
           ui.lead("Levenshtein distance adds up the one-letter edits (replace, remove or insert) needed to turn the typed "
                   "text into the name. Lower is closer. The search puts the name with the lowest distance first."),
           ui.columns(
               ui.card(ill.waterfall([(f"“{fmt.esc(ex['query'])}”", 0, "base"), ("w in place of ã", 1, "delta"),
                                      ("missing P of Preto", 1, "delta"), ("distance to the name", ex["distance"], "total")],
                                     w=470, f=lambda v: num(v), illustrative_=False, scale_max=3),
                       kicker=f"Query with 2 errors → {fmt.esc(ex['name'])}", variant="tint"),
               ui.card(ill.waterfall([(f"“{fmt.esc(tr['query'])}”", 0, "base"), ("e in place of O", 1, "delta"),
                                      ("O in place of e", 1, "delta"), ("distance to the name", tr["distance"], "total")],
                                     w=470, f=lambda v: num(v), illustrative_=False, scale_max=3),
                       kicker=f"Query with 1 error (swapped letters) → {fmt.esc(tr['name'])}", variant="tint")),
           ui.how_to_read("Swapping two neighboring letters is a single slip for whoever types, but Levenshtein distance counts "
                          "two edits. That gap shows up again in the results."),
           source="Real examples from the query set; distances computed on lowercase text.")

# 5. Concept: the queue and first place
easy, hard = R["queue"]
deck.slide("What ranking is", "For whoever searches, what matters is the right name being first in the candidate queue",
           ill.queue_scenarios([("Exact match", {9}, "ties with every name"),
                                (f"1 error: “{fmt.esc(easy['query'])}”", {easy["rank"] - 1}, f"right name {nth(easy['rank'])}"),
                                (f"3 errors: “{fmt.esc(hard['query'])}”", {hard["rank"] - 1}, f"right name {nth(hard['rank'])}")],
                               axis=("lowest distance", "highest distance"), legends=("right name", "other names"),
                               label="The first 20 candidates of each query. For real queries the position is the measure; for exact "
                                     "matching the right name ties with all of them and the position shown is illustrative."),
           ui.columns(
               ui.how_to_read([f"Each queue has all {num(NEG + 1)} names, from nearest to farthest.",
                               f"<b>Ranking (AUC)</b> measures the whole queue: on average {dec(R['names_ahead'], 1)} wrong name "
                               f"lands ahead of the right one, out of {num(NEG)}.",
                               "<b>Right name first</b> measures only the front of the queue, which is what people see."]),
               ui.how_to_read(f"“{fmt.esc(hard['query'])}” is 2 edits from {fmt.esc(hard['first'][0][0])} and 3 from "
                              f"{fmt.esc(hard['first'][1][0])}, {fmt.esc(hard['first'][2][0])} and {fmt.esc(hard['name'])}: "
                              f"the right name ties with two others and falls to {nth(hard['rank'])}.",
                              f"In the 3-error query ({fmt.esc(hard['name'])})")),
           source="Real queries from the set; ties at the same distance broken alphabetically in this illustration only.")

# 6. The three measures
deck.slide("The three measures", "Three numbers sum up the search: first place, the top 5, and the ranking of the whole queue",
           ui.measures([
               ("Right name first", pct(G["top1"]), "Out of 100 queries with typos, how many have the right name first.",
                ill.scale(G["top1"], 0, 1, refs=[(X["top1"], f"exact match: {pct(X['top1'])}")], ends=("0%", "100%"), f=pct),
                "Higher is better."),
               ("In the top 5", f"{round(100 * G['top5'])} of 100", "How many show the right name in a list of 5 suggestions.",
                ill.grid(100 * G["top5"]), "Higher is better."),
               ("Ranking · AUC", dec(G["auc"], 4), "Between a wrong name and the right one, the chance the right one comes first.",
                ui.big(dec(R["names_ahead"], 1), f"wrong name ahead of the right one, on average, out of {num(NEG)}"),
                "Closer to 1 is better. 0.5 is a coin flip."),
           ]),
           source=SOURCE_ERR)

# 7. First place drops with each error
xs = ["0", "1", "2", "3"]
err_label = lambda e: f"{e} error" + ("" if e == "1" else "s")  # noqa: E731
deck.slide("Typing errors", f"Each extra error lowers first-place hits: from {pct(BY_E['1']['top1'])} with 1 error "
                            f"to {pct(BY_E['3']['top1'])} with 3",
           ill.small_multiples([
               {"title": "Right name first", "points": [(e, BY_E[e]["top1"]) for e in xs], "ydom": (0.7, 1.0),
                "yticks": [0.7, 0.8, 0.9, 1.0], "yfmt": lambda v: pct(v, 0), "hollow": {"0"}},
               {"title": "In the top 5", "points": [(e, BY_E[e]["top5"]) for e in xs], "ydom": (0.85, 1.0),
                "yticks": [0.85, 0.9, 0.95, 1.0], "yfmt": lambda v: pct(v, 0), "hollow": {"0"}},
               {"title": "Ranking · AUC", "points": [(e, BY_E[e]["auc"]) for e in xs], "ydom": (0.999, 1.0),
                "yticks": [0.999, 0.9995, 1.0], "yfmt": lambda v: dec(v, 4), "hollow": {"0"}},
           ], xfmt=err_label, w=356, h=290),
           ui.paragraph(f"With 3 errors, the right name is still in the top 5 for {pct(BY_E['3']['top5'])} of queries. "
                        "Hollow points: queries without errors, only as a reference."),
           source=f"{SOURCE} {num(R['municipalities'])} queries per number of errors, lowercase text.")

# 8. What the names look like
comp = R["composition"]
order = ["one word, no accent", "one word, with accent", "compound, no accent", "compound, with accent"]
deck.slide("Which names", f"{pct(R['with_accent'], 0)} of the names have an accent and {pct(R['compound'], 0)} have more than one word",
           ui.columns(
               ui.stack(ui.chart_title("How municipalities split by name shape"),
                        ill.composition([(cap(k), comp[k]) for k in order], w=560, label_min=9999, with_legend=True)),
               ui.stack(ui.chart_title("% of names with an accent, by region"),
                        ill.availability([(g, v) for g, v in R["accent_by_region"].items()], w=500)),
               widths=("560px", "1fr"), gap=40),
           ui.how_to_read(f"Accent, length and region are the cuts of the next pages. {pct(R['repeated'])} of municipalities share "
                          "their name with another municipality in another state: by name alone, the search cannot tell them apart."),
           source=SOURCE)

# 9. By region
rows_reg = [{"name": g, "sub": f"{num(v['municipalities'])} municipalities · names of {dec(v['mean_length'], 1)} letters on average",
             "share": v["municipalities"] / R["municipalities"], "value": v["top1_raw"],
             "ci": fmt.wilson(v["hits_raw"], v["queries"]), "extras": [pct(v["top1_folded"]), num(v["queries"])]}
            for g, v in REG.items()]
lo = min(REG, key=lambda g: REG[g]["top1_raw"])
hi = max(REG, key=lambda g: REG[g]["top1_raw"])
deck.slide("By region", f"First-place hits go from {pct(REG[lo]['top1_raw'])} in the {lo} to {pct(REG[hi]['top1_raw'])} in the {hi}",
           ill.segment_table(rows_reg, (0.80, 0.90), header=("Region", "% of municipalities", "Right name first · 95% CI"),
                             extras=("Accents removed", "Queries")),
           ui.how_to_read(f"The dot is the first-place rate; the line, its 95% confidence interval. Intervals that do not overlap, "
                          f"like the {lo}'s and the {hi}'s, point to a difference beyond chance. Mean name length barely varies "
                          "across regions and does not follow the rate; the cause of the difference was not investigated."),
           source=SOURCE_ERR)

# 10. Short names concentrate the misses
deck.slide("Name length", f"Names of up to 6 letters are {pct(SHORT['pct_queries'], 0)} of queries and "
                          f"{pct(SHORT['pct_misses'], 0)} of the misses",
           ui.columns(
               ill.paired_bars([(f["band"], f["pct_queries"], f["pct_misses"], f"miss {pct(f['miss'])}") for f in R["length"]],
                               labels=("% of queries", "% of first-place misses"), w=740, h=300),
               ui.stack(ill.concentration_bars(MISS_MEAN, SHORT["miss"], labels=("All names", "Up to 6 letters"), w=300, h=200),
                        ui.how_to_read(f"A colored bar taller than the grey one means the band concentrates misses. For names of up "
                                       f"to 6 letters the miss rate is {pct(SHORT['miss'])}, {fmt.mult(SHORT['miss'] / MISS_MEAN)} the "
                                       "average: each error weighs more in a short name, and more names sit a few edits away.")),
               widths=("740px", "1fr"), gap=28),
           source=SOURCE_ERR + " Length in characters, spaces included.")

# 11. Length x errors
heat = R["heat"]
lowest = min(v for row in heat["values"] for v in row)
deck.slide("Length × errors", f"With 3 errors, names of up to 6 letters come first in {pct(heat['values'][0][2], 0)} of queries",
           ui.columns(
               ui.stack(ui.chart_title("% of queries with the right name first, by name length (letters)"),
                        ill.heatmap(heat["rows"], heat["cols"], heat["values"], f=pct,
                                    intensity=lambda v: (1 - v) / (1 - lowest), label_w=110, cell_w=110, cell_h=44),
                        ui.note("Stronger color: more misses.")),
               ui.stack(ui.chart_title("Right name first: lowercase × accents removed"),
                        ill.lines([("Lowercase", t.primary, [(e, R["by_errors"]["raw"][e]["top1"]) for e in xs]),
                                   ("No accents", t.n500, [(e, R["by_errors"]["folded"][e]["top1"]) for e in xs])],
                                  470, 280, (0.7, 1.0), [0.7, 0.8, 0.9, 1.0], lambda v: pct(v, 0), xfmt=err_label, mr=110)),
               widths=("1fr", "480px"), gap=32),
           source=f"{SOURCE} {num(R['municipalities'])} queries per number of errors.")

# 12. Error kinds
kinds = sorted(KINDS, key=lambda k: -KINDS[k]["miss_raw"])
deck.slide("Error kinds", f"With 1 error, a swap pushes the right name out of first place in {pct(KINDS['transposition']['miss_raw'])} "
                          f"of queries, {fmt.mult(KINDS['transposition']['miss_raw'] / KINDS['deletion']['miss_raw'])} a deletion",
           ui.columns(
               ui.stack(ui.chart_title("% of 1-error queries where the right name lost first place, by error kind"),
                        ill.weights([(cap(k), KINDS[k]["miss_raw"]) for k in kinds], f=pct, w=640, label_w=200),
                        ui.note("; ".join(f"{k}: {num(KINDS[k]['queries'])} queries" for k in kinds) + ".")),
               ui.stack(ui.how_to_read(["<b>Longer bar</b>: the kind of error that most often knocks the right name out of first.",
                                        "<b>Transposition</b>: swapping two neighboring letters counts as 2 Levenshtein edits.",
                                        "<b>Accent</b>: on lowercase text, each missing accented letter counts as 1 edit."],
                                       "How to read"),
                        ui.card("The Damerau variant, which counts a swap as 1 edit, should reduce these misses. It is a "
                                "hypothesis: it was not measured here.", kicker="Hypothesis to test", variant="outline")),
               widths=("640px", "1fr"), gap=28),
           source=f"{SOURCE} {num(sum(v['queries'] for v in KINDS.values()))} queries with 1 error, lowercase text.")

# 13. Why removing accents did not help
deck.slide("Removing accents", f"Removing accents fixes accent errors but raises misses for the other kinds: "
                               f"{pct(N['top1'])} against {pct(G['top1'])} overall",
           ui.columns(
               ill.paired_bars([(cap(k), KINDS[k]["miss_raw"], KINDS[k]["miss_folded"], f"{num(KINDS[k]['queries'])} queries")
                                for k in kinds], labels=("% misses · lowercase", "% misses · no accents"), w=740, h=300, d=1),
               ui.stack(ui.how_to_read(f"Without accents, accent errors almost vanish ({pct(KINDS['accent']['miss_raw'])} → "
                                       f"{pct(KINDS['accent']['miss_folded'])}). For the other kinds, misses go up: for swaps, "
                                       f"from {pct(KINDS['transposition']['miss_raw'])} to {pct(KINDS['transposition']['miss_folded'])}.",
                                       "What changed"),
                        ui.card("When people type the accent, it helps separate similar names; removing it brings more names "
                                "close to the query. For: misses rise for every kind except accents. Not measured: how many "
                                "extra ties appear.", kicker="Hypothesis", variant="outline")),
               widths=("740px", "1fr"), gap=28),
           source=f"{SOURCE} Queries with 1 error; no accents also means no hyphens and apostrophes.")

# 14. Verdict
deck.slide("Verdict", "Strengths and limits",
           ui.strengths_limits(
               [f"Ranks the right name first in {pct(G['top1'])} of queries with 1 to 3 errors; exact matching gets {pct(X['top1'])}.",
                f"With 1 error, first in {pct(U['top1'])} and in the top 5 in {pct(U['top5'])}.",
                f"Names of 13 letters or more almost never miss (up to {pct(R['length'][3]['miss'])} misses)."],
               [f"Names of up to 6 letters are {pct(SHORT['pct_misses'], 0)} of misses, with {pct(SHORT['pct_queries'], 0)} of queries.",
                f"Swapping neighboring letters counts as 2 edits: {pct(KINDS['transposition']['miss_raw'])} misses with 1 error.",
                f"By name alone, it cannot tell apart municipalities that share a name ({pct(R['repeated'])} of them)."],
               verdict_line="Verdict: <b>good for suggesting</b> a list of municipalities; for correcting the query without "
                            f"confirmation, the first-place rate ({pct(G['top1'])}) leaves about 1 query wrong in every "
                            f"{round(1 / (1 - G['top1']))}."),
           source=SOURCE_ERR)

# 15. How to use it today
deck.slide("How to use it today", "Use the search to suggest a list of names, not to correct the query on its own",
           ui.columns(
               ui.use_for([f"show the 5 nearest names as suggestions: the right one is among them in {pct(G['top5'])} of queries"],
                          ["replace the query with the first name without confirmation, or pick between same-name municipalities without the state"]),
               ui.card(ui.columns(ill.grid(100 * G["top1"], size=15, gap=6),
                                  f"Out of 100 queries with typos, <b>{round(100 * G['top1'])}</b> bring the right name first. "
                                  f"In a list of 5 suggestions, <b>{round(100 * G['top5'])}</b>.", widths=("230px", "1fr"),
                                  align="center"),
                       kicker="Why", variant="tint"),
               widths=("1fr", "1.15fr"), gap=28),
           source=SOURCE_ERR)

# 16. Next steps
deck.slide("Next steps", "Proposed next steps",
           ui.proposals([
               ("Count a swap of letters as 1 edit (Damerau)",
                f"A swap pushes the right name out of first place in {pct(KINDS['transposition']['miss_raw'])} of 1-error queries.",
                "the gain being measured on these same queries", "sliders"),
               ("Remove accents only when the query has none",
                "Keeps the gain on accent errors without losing what a typed accent tells.",
                "the overall result beating lowercase on the same queries", "text"),
               ("Ask for or infer the state for shared names",
                f"{pct(R['repeated'])} of municipalities share their name with another one in another state.",
                "the search having the state or the person's location", "pin"),
               ("Show 5 suggestions instead of correcting",
                f"The right name is in the top 5 in {pct(G['top5'])} of queries with typos.",
                "the interface letting people choose", "search"),
           ]),
           source=SOURCE_ERR)

# 17. Close
deck.closing("Fuzzy search over municipality names",
             ["A cutroom-deck example, made with cutroom.",
              "Data: IBGE's list of municipalities. Code and numbers: examples/deck-fuzzy-search/src."],
             signature="github.com/galvaowesley/cutroom")
