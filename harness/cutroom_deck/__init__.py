"""cutroom_deck: 16:9 PDF presentations in the active brand, from a Python script (skill cutroom-deck).

    from cutroom_deck import Deck, Theme, ui, ill, fmt

    deck = Deck("Piece title", footer="Team · Piece · edition", slug="my-piece")
    deck.cover("Eyebrow", "Cover title", "Subtitle", "meta: period, source")
    deck.slide("Summary", "The slide's message with the number", ui.lead("..."), source="Source: ..., period")
    deck.closing("Final message", ["contact"], signature="Team")

Build with `deck build <piece folder>` (reads src/deck.py), then `deck check` and `deck preview`.
Another brand: Deck(..., theme=Theme.from_brand("paper")).
"""
from . import fmt, ill, ui
from .render import Deck
from .theme import Theme, active, use

__all__ = ["Deck", "Theme", "active", "use", "fmt", "ill", "ui"]
