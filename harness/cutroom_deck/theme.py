"""Deck theme: colors, fonts and logos, read from a brand (default: the active brand, `cutroom brand use`).

Another identity: Theme.from_brand("acme") for any brand in `cutroom brand list`, Theme.from_brand("path/to/folder")
for a brand folder, or Theme.from_brand().with_(primary="#0055AA", ...) for a one-off change. Illustrations and CSS
only read the active theme, never fixed colors.
"""
import sys
from dataclasses import dataclass, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cutroom_brand  # noqa: E402


@dataclass(frozen=True)
class Theme:
    # Colors (the brand's DESIGN.md says how to use them): primary is constant, deep frames the verdict, accent
    # only highlights.
    primary: str = "#3B4CCA"
    deep: str = "#121A3A"
    accent: str = "#FF6B4A"
    accent_soft: str = "#A9B4FF"
    tint: str = "#EEF0FC"                       # "how to read" boxes and highlights
    scale: tuple = ("#EEF0FC", "#D9DEFA", "#B3BCF3", "#8592E6", "#5C6CD8", "#3B4CCA")  # ordinal, light -> dark
    background: str = "#FFFFFF"
    on_primary: str = "#FFFFFF"
    on_deep: str = "#FFFFFF"
    n100: str = "#F2F3F7"
    n200: str = "#E3E5EC"
    n300: str = "#C9CDD8"
    n500: str = "#737A8E"
    n700: str = "#3E4456"
    n900: str = "#14161F"
    # Semantic: only in "use for / don't use for" and "strengths / limits".
    success: str = "#17784C"
    success_bg: str = "#E3F4EB"
    danger: str = "#B42A36"
    danger_bg: str = "#FBE5E7"
    warning: str = "#7D5200"
    warning_bg: str = "#FFF3D6"
    # Type
    font_display: str = "Inter Tight"
    font_text: str = "Inter"
    font_mono: str = "JetBrains Mono NL"
    font_files: tuple = ()                      # (family, file relative to `folder`, CSS weight, style)
    radius: int = 16
    # Logos: on_primary on the cover, on_light on the closing slide; nowhere else.
    logo_cover: str = ""
    logo_closing: str = ""
    cover_glow: bool = True                     # soft radial of accent in a corner of the cover
    folder: str = ""                            # base folder of font and logo files

    @classmethod
    def from_brand(cls, name=None):
        m = cutroom_brand.load(name)
        c, f = m["colors"], m.get("fonts", {})
        n = c["neutral"]
        return cls(
            primary=c["primary"], deep=c["deep"], accent=c["accent"], accent_soft=c["accent_soft"], tint=c["tint"],
            scale=tuple(c["scale"]), background=c["background"], on_primary=c["on_primary"], on_deep=c["on_deep"],
            n100=n["100"], n200=n["200"], n300=n["300"], n500=n["500"], n700=n["700"], n900=n["900"],
            success=c["success"], success_bg=c["success_bg"], danger=c["danger"], danger_bg=c["danger_bg"],
            warning=c["warning"], warning_bg=c["warning_bg"],
            font_display=f.get("display", "sans-serif"), font_text=f.get("text", "sans-serif"),
            font_mono=f.get("mono", "monospace"),
            font_files=tuple((x["family"], x["file"], str(x.get("weight", "400")), x.get("style", "normal"))
                             for x in f.get("files", [])),
            radius=m["shape"]["radius"],
            logo_cover=m["logos"].get("on_primary") or "", logo_closing=m["logos"].get("on_light") or "",
            cover_glow=m["cover"]["glow"], folder=m["dir"])

    def with_(self, **kw):
        return replace(self, **kw)

    def file(self, rel):
        return Path(self.folder) / rel


_active = None


def active():
    global _active
    if _active is None:
        _active = Theme.from_brand()
    return _active


def use(theme):
    global _active
    _active = theme
    return theme
