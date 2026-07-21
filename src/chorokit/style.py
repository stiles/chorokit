from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib as mpl
from matplotlib import font_manager

_FONT_DIR = Path(__file__).resolve().parent / "fonts"
_BARLOW_FILES = ("Barlow-Regular.ttf", "Barlow-SemiBold.ttf", "Barlow-Bold.ttf")
_barlow_registered = False


def register_barlow() -> bool:
    """Register the bundled Barlow faces with matplotlib.

    Returns True if Barlow is available afterward.
    """
    global _barlow_registered
    if _barlow_registered:
        return True
    found = False
    for name in _BARLOW_FILES:
        path = _FONT_DIR / name
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            found = True
    _barlow_registered = found
    return found


@dataclass
class Theme:
    """Typography and color defaults for chorokit figures.

    Barlow ships with the package so maps look the same on every machine.
    Pass another ``font_family`` (e.g. ``"DejaVu Sans"``) to override.
    """

    font_family: Optional[str] = "Barlow"
    title_fontsize: int = 18
    title_weight: str = "bold"
    subtitle_fontsize: int = 12
    source_fontsize: int = 9
    text_color: str = "#333"
    quiet_color: str = "#666"

    def apply(self) -> None:
        family = self.font_family
        if family == "Barlow":
            if not register_barlow():
                family = "DejaVu Sans"
        if family:
            mpl.rcParams["font.family"] = family
            mpl.rcParams["text.color"] = self.text_color
