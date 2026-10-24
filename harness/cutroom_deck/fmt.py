"""Numbers and dates, in the deck's language (English by default; pt, es, fr, de, it use a decimal comma).

Rounding rule: add and divide raw values, format only at the end.
E.g. pct(0.0726 + 0.0218) gives "9.4%"; pct(0.0726) and pct(0.0218) added by hand would give 9.5%.
"""
import html
import math

_locale = "en"
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
}
MONTHS_LONG = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
           "novembro", "dezembro"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"],
}
COMMA_DECIMAL = {"pt", "es", "fr", "de", "it", "nl"}
WORDS = {"en": ("to", "95% CI: "), "pt": ("a", "IC 95%: "), "es": ("a", "IC 95%: ")}


def set_locale(lang):
    """"en", "en-GB", "pt-BR"... Only the language part matters."""
    global _locale
    _locale = (lang or "en").split("-")[0].lower()


def locale():
    return _locale


def esc(s):
    """Escape text coming from data (names, labels) before putting it in HTML or SVG."""
    return html.escape(str(s), quote=True)


def num(v, d=0):
    """5571 -> "5,571" (en) or "5.571" (pt); 1234.5, d=1 -> "1,234.5" or "1.234,5"."""
    s = f"{v:,.{d}f}"
    if _locale in COMMA_DECIMAL:
        s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return s


def dec(v, d=2):
    """0.5912 -> "0.59"."""
    return num(v, d)


def pct(v, d=1, sign=False):
    """Fraction -> percent: 0.094 -> "9.4%". sign=True adds "+" to positives."""
    s = num(100 * v, d) + "%"
    return ("+" + s) if sign and v > 0 else s


def mult(v, d=1):
    """2.31 -> "2.3x" (lift, ratio)."""
    return num(v, d) + "x"


def size(bytes_, d=1):
    """Bytes in B, KB, MB or GB (base 1024, like du -h): 1536 -> "1.5 KB"; 3_840_000_000 -> "3.6 GB"."""
    v, unit = float(bytes_), "B"
    for u in ("KB", "MB", "GB", "TB"):
        if v < 1024:
            break
        v, unit = v / 1024, u
    return f"{num(v, 0 if unit == 'B' else d)} {unit}"


def duration(s, d=1):
    """Seconds as "14.0 s", "1 min 4 s" or "1 h 2 min". d = decimals under 1 min."""
    if s < 60:
        return f"{num(s, d)} s"
    if s < 3600:
        m, r = divmod(round(s), 60)
        return f"{m} min" + (f" {r} s" if r else "")
    h, r = divmod(round(s / 60), 60)
    return f"{h} h" + (f" {r} min" if r else "")


def date(iso):
    """"2026-06-28" -> "Jun 28, 2026" (en) or "28/06/2026"."""
    if _locale == "en":
        return f"{MONTHS['en'][int(iso[5:7]) - 1]} {int(iso[8:10])}, {iso[:4]}"
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


def month(iso):
    """"2026-06-28" -> "Jun 26" (en) or "jun/26"."""
    names = MONTHS.get(_locale, MONTHS["en"])[int(iso[5:7]) - 1]
    return f"{names} {iso[2:4]}" if _locale == "en" else f"{names}/{iso[2:4]}"


def month_long(iso):
    """"2026-06-28" -> "June 2026" (en) or "junho de 2026" (pt)."""
    name = MONTHS_LONG.get(_locale, MONTHS_LONG["en"])[int(iso[5:7]) - 1]
    return f"{name} {iso[:4]}" if _locale == "en" else f"{name} de {iso[:4]}"


def wilson(k, n, z=1.96):
    """Wilson confidence interval (95% by default) for the proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, center - half), min(1.0, center + half))


def ci(lo, hi, f=pct, prefix=None):
    """(0.612, 0.640) -> "95% CI: 61.2% to 64.0%"."""
    to, pre = WORDS.get(_locale, WORDS["en"])
    return f"{pre if prefix is None else prefix}{f(lo)} {to} {f(hi)}"
