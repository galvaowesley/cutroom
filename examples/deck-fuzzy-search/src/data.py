#!/usr/bin/env python3
"""Measures fuzzy search over Brazilian municipality names and writes results.json for the deck.

Input: ibge_municipalities.csv (the official list from IBGE, Brazil's statistics office, localities API, downloaded
on 2026-10-21). For every municipality, a query with 0, 1, 2 and 3 typing errors (fixed seed), and the 5,298
distinct names ranked by three methods:
  exact   right only if the text is identical (the rest tie);
  raw     Levenshtein distance on the lowercase text;
  folded  Levenshtein after removing accents, hyphens and apostrophes.
Measures per query (ties broken at random, in expectation): AUC (share of wrong names ranked after the right one),
right name first, and right name in the top 5.

Usage: python3 data.py   (about 1 to 2 min on 16 cores; standard library only)
"""
import csv
import json
import random
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 2026
KINDS = ["accent", "deletion", "insertion", "substitution", "transposition"]
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_raw(s):
    return s.lower()


def norm_folded(s):
    s = strip_accents(s.lower()).replace("-", " ").replace("'", " ")
    return " ".join(s.split())


def distance_upto(a, b, limit):
    """Levenshtein of a and b, or limit + 1 once it passes the limit (stops early)."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        low = i
        for j, cb in enumerate(b, 1):
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            cur[j] = v
            low = min(low, v)
        if low > limit:
            return limit + 1
        prev = cur
    return prev[-1] if prev[-1] <= limit else limit + 1


def corrupt(name, errors, rng):
    """Apply `errors` typing errors; return (query, kinds applied)."""
    s, kinds = name, []
    for _ in range(errors):
        options = [t for t in KINDS if t != "accent" or strip_accents(s) != s]
        t = rng.choice(options)
        letters = [i for i, c in enumerate(s) if c.isalpha()]
        i = rng.choice(letters)
        if t == "accent":
            s = strip_accents(s)
        elif t == "deletion":
            s = s[:i] + s[i + 1:]
        elif t == "insertion":
            s = s[:i] + rng.choice(LETTERS) + s[i:]
        elif t == "substitution":
            s = s[:i] + rng.choice([c for c in LETTERS if c != s[i].lower()]) + s[i + 1:]
        elif t == "transposition":
            if i + 1 < len(s) and s[i + 1].isalpha() and s[i] != s[i + 1]:
                s = s[:i] + s[i + 1] + s[i] + s[i + 2:]
            else:
                s = s[:i] + s[i + 1:]
                t = "deletion"
        kinds.append(t)
    return s, kinds


NAMES = []
FORMS = {}


def _init(names):
    global NAMES, FORMS
    NAMES = names
    FORMS = {"raw": [norm_raw(n) for n in names], "folded": [norm_folded(n) for n in names]}


def measure(task):
    """One query: the measures of the three methods."""
    right, query = task
    n_neg = len(NAMES) - 1
    out = {}
    # exact: distance 0 if equal, 1 otherwise
    equal = sum(1 for k, n in enumerate(NAMES) if k != right and n == query)
    dc = 0 if NAMES[right] == query else 1
    ahead = equal if dc == 1 else 0
    ties = (n_neg - equal) if dc == 1 else equal
    out["exact"] = (ahead, ties)
    for method, f in (("raw", norm_raw), ("folded", norm_folded)):
        q, forms = f(query), FORMS[method]
        dc = distance_upto(q, forms[right], 40)
        ahead = ties = 0
        for k, b in enumerate(forms):
            if k == right:
                continue
            d = distance_upto(q, b, dc)
            if d < dc:
                ahead += 1
            elif d == dc:
                ties += 1
        out[method] = (ahead, ties)
    res = {}
    for m, (ahead, ties) in out.items():
        res[m] = {
            "auc": (n_neg - ahead - ties + 0.5 * ties) / n_neg,
            "top1": (1 / (ties + 1)) if ahead == 0 else 0.0,
            "top5": max(0.0, min(1.0, (5 - ahead) / (ties + 1))),
        }
    return res


def main():
    rows = list(csv.DictReader(open(HERE / "ibge_municipalities.csv", encoding="utf-8")))
    names = sorted({r["nome"] for r in rows})
    pos = {n: i for i, n in enumerate(names)}
    rng = random.Random(SEED)
    queries = []
    for r in rows:
        for e in range(4):
            q, kinds = corrupt(r["nome"], e, rng)
            queries.append({"name": r["nome"], "state": r["uf"], "region": r["regiao"], "errors": e, "kinds": kinds, "query": q})
    with ProcessPoolExecutor(initializer=_init, initargs=(names,)) as ex:
        measures = list(ex.map(measure, [(pos[q["name"]], q["query"]) for q in queries], chunksize=64))
    for q, m in zip(queries, measures):
        q["m"] = m

    def mean(qs, method, what):
        return sum(q["m"][method][what] for q in qs) / len(qs) if qs else None

    def misses(qs, method):
        return sum(1 - q["m"][method]["top1"] for q in qs)

    count = Counter(r["nome"] for r in rows)
    with_errors = [q for q in queries if q["errors"] >= 1]
    one_error = [q for q in queries if q["errors"] == 1]
    methods = ["exact", "raw", "folded"]
    res = {
        "source": "IBGE, localities API (servicodados.ibge.gov.br/api/v1/localidades/municipios)",
        "downloaded": "2026-10-21",
        "seed": SEED,
        "municipalities": len(rows),
        "distinct_names": len(names),
        "queries": len(queries),
        "with_accent": sum(1 for r in rows if strip_accents(r["nome"]) != r["nome"]) / len(rows),
        "compound": sum(1 for r in rows if " " in r["nome"] or "-" in r["nome"]) / len(rows),
        "repeated": sum(1 for r in rows if count[r["nome"]] > 1) / len(rows),
        "overall": {m: {k: mean(with_errors, m, k) for k in ("auc", "top1", "top5")} for m in methods},
        "one_error": {m: {k: mean(one_error, m, k) for k in ("auc", "top1", "top5")} for m in methods},
        "by_errors": {m: {str(e): {k: mean([q for q in queries if q["errors"] == e], m, k) for k in ("auc", "top1", "top5")}
                          for e in range(4)} for m in methods},
    }
    # composition of the base: words x accent (a partition)
    comp = defaultdict(int)
    for r in rows:
        compound = " " in r["nome"] or "-" in r["nome"]
        accent = strip_accents(r["nome"]) != r["nome"]
        comp[("compound" if compound else "one word") + (", with accent" if accent else ", no accent")] += 1
    res["composition"] = {k: v / len(rows) for k, v in comp.items()}
    regions = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    res["accent_by_region"] = {g: sum(1 for r in rows if r["regiao"] == g and strip_accents(r["nome"]) != r["nome"])
                               / sum(1 for r in rows if r["regiao"] == g) for g in regions}
    # by region, queries with 1 to 3 errors
    res["by_region"] = {}
    for g in regions:
        qs = [q for q in with_errors if q["region"] == g]
        res["by_region"][g] = {"municipalities": sum(1 for r in rows if r["regiao"] == g), "queries": len(qs),
                               "top1_raw": mean(qs, "raw", "top1"), "hits_raw": sum(q["m"]["raw"]["top1"] for q in qs),
                               "top1_folded": mean(qs, "folded", "top1"),
                               "mean_length": sum(len(r["nome"]) for r in rows if r["regiao"] == g)
                               / sum(1 for r in rows if r["regiao"] == g)}
    res["miss_raw_mean"] = misses(with_errors, "raw") / len(with_errors)
    # heatmap: right name first (raw) by name length x errors
    bands = [(1, 6, "up to 6"), (7, 9, "7 to 9"), (10, 12, "10 to 12"), (13, 16, "13 to 16"), (17, 99, "17 or more")]
    res["heat"] = {"rows": [b[2] for b in bands], "cols": ["1 error", "2 errors", "3 errors"],
                   "values": [[mean([q for q in queries if q["errors"] == e and a <= len(q["name"]) <= b], "raw", "top1")
                               for e in (1, 2, 3)] for a, b, _ in bands]}
    # length bands (queries with 1 to 3 errors, raw): % of queries x % of misses
    tot = misses(with_errors, "raw")
    res["length"] = []
    for a, b, label in bands:
        qs = [q for q in with_errors if a <= len(q["name"]) <= b]
        res["length"].append({"band": label, "pct_queries": len(qs) / len(with_errors), "pct_misses": misses(qs, "raw") / tot,
                              "miss": misses(qs, "raw") / len(qs)})
    res["names_ahead"] = (1 - res["overall"]["raw"]["auc"]) * (len(names) - 1)
    # by error kind (queries with 1 error): misses at first place
    res["by_kind"] = {}
    for t in KINDS:
        qs = [q for q in one_error if q["kinds"] == [t]]
        res["by_kind"][t] = {"queries": len(qs), "miss_raw": misses(qs, "raw") / len(qs) if qs else None,
                             "miss_folded": misses(qs, "folded") / len(qs) if qs else None}
    # real examples: the distance waterfall and the right name's place in the queue (alphabetical tie-break)
    _init(names)

    def real_queue(q):
        s, forms = norm_raw(q["query"]), FORMS["raw"]
        ds = sorted((distance_upto(s, b, 40), names[k]) for k, b in enumerate(forms))
        rank = next(i for i, (_, n) in enumerate(ds) if n == q["name"]) + 1
        return rank, [(n, d) for d, n in ds[:6]]
    ex = next(q for q in queries if q["name"] == "São José do Rio Preto" and q["errors"] == 2)
    res["example"] = {"name": ex["name"], "query": ex["query"], "kinds": ex["kinds"],
                      "distance": distance_upto(norm_raw(ex["query"]), norm_raw(ex["name"]), 40)}
    tr = next(q for q in one_error if q["kinds"] == ["transposition"] and len(q["name"]) >= 7)
    res["example_transposition"] = {"name": tr["name"], "query": tr["query"],
                                    "distance": distance_upto(norm_raw(tr["query"]), norm_raw(tr["name"]), 40)}
    easy = next(q for q in one_error if q["kinds"] == ["substitution"] and real_queue(q)[0] == 1)
    hard = next(q for q in queries if q["errors"] == 3 and len(q["name"]) <= 6 and 3 <= real_queue(q)[0] <= 6)
    res["queue"] = [{"name": q["name"], "query": q["query"], "errors": q["errors"], "rank": real_queue(q)[0],
                     "first": real_queue(q)[1]} for q in (easy, hard)]
    (HERE / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("overall", "one_error")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
