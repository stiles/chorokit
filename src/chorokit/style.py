from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import matplotlib as mpl


@dataclass
class Theme:
    """Basic typography and spacing defaults.

    This is intentionally small; callers can override fields as needed.
    """

    font_family: Optional[str] = "Roboto, Arial"
    title_fontsize: int = 18
    title_weight: str = "bold"
    subtitle_fontsize: int = 12
    source_fontsize: int = 9
    text_color: str = "#333"
    quiet_color: str = "#666"

    def apply(self) -> None:
        if self.font_family:
            mpl.rcParams["font.family"] = self.font_family


