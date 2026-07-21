"""Deterministic figure layout computed in physical units.

The figure is a vertical stack of bands measured in inches:

    top margin
    title
    subtitle
    legend (if location == "top")
    map
    legend (if location == "bottom")
    source / credit
    bottom margin

The caller supplies a figure width; the map height comes from the projected
data's aspect ratio, and the figure height is the sum of the bands. Because
every band has a fixed physical size, spacing is identical for any geography,
text combination or figure width - no figure-fraction constants involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .style import Theme

# vertical rhythm (inches)
GAP_AFTER_TITLE = 0.10
GAP_AFTER_TEXT_BLOCK = 0.22
GAP_LEGEND_TO_MAP = 0.18
GAP_MAP_TO_FOOTER = 0.14
LINE_SPACING = 1.35  # multiple of font size

# legend geometry (inches)
LEGEND_BAR_HEIGHT = 0.16
LEGEND_MAX_WIDTH = 3.5
LEGEND_TITLE_PAD = 0.08
LEGEND_TICK_PAD = 0.06

# guard against absurd canvases from sliver geographies
DEFAULT_MAX_HEIGHT_RATIO = 1.4
MIN_MAP_HEIGHT = 1.0


def _pt_to_in(points: float) -> float:
    return points / 72.0


@dataclass(frozen=True)
class LegendSpec:
    """Physical description of the legend block."""

    location: str  # "top" or "bottom"
    has_title: bool
    align: str = "center"  # "center" or "left"
    title_fontsize: int = 10
    tick_fontsize: int = 9

    @property
    def title_space(self) -> float:
        if not self.has_title:
            return 0.0
        return _pt_to_in(self.title_fontsize) * LINE_SPACING + LEGEND_TITLE_PAD

    @property
    def tick_space(self) -> float:
        return _pt_to_in(self.tick_fontsize) * LINE_SPACING + LEGEND_TICK_PAD

    @property
    def block_height(self) -> float:
        return self.title_space + LEGEND_BAR_HEIGHT + self.tick_space


@dataclass(frozen=True)
class ComputedLayout:
    """Figure size plus rectangles and anchors in figure fractions."""

    fig_width: float
    fig_height: float
    map_rect: Tuple[float, float, float, float]
    legend_rect: Optional[Tuple[float, float, float, float]]
    # (x, y) anchors, va="top" for header text, va="bottom" for footer text
    title_pos: Optional[Tuple[float, float]]
    subtitle_pos: Optional[Tuple[float, float]]
    source_pos: Optional[Tuple[float, float]]
    credit_pos: Optional[Tuple[float, float]]


def compute_layout(
    map_aspect: float,
    *,
    width: float,
    margins: Tuple[float, float, float, float],
    theme: Theme,
    has_title: bool,
    has_subtitle: bool,
    has_source: bool,
    has_credit: bool,
    legend: Optional[LegendSpec] = None,
    max_height: Optional[float] = None,
) -> ComputedLayout:
    """Compute figure size and element rectangles.

    map_aspect is width/height of the projected data bounds. margins are
    (left, right, bottom, top) in inches.
    """
    if map_aspect <= 0:
        map_aspect = 1.0
    left, right, bottom, top = margins
    content_w = max(width - left - right, 0.5)

    # header stack: distance from figure top to the top of the map (inches)
    y = top
    title_y = None
    subtitle_y = None
    if has_title:
        title_y = y
        y += _pt_to_in(theme.title_fontsize) * LINE_SPACING
        if has_subtitle:
            y += GAP_AFTER_TITLE
    if has_subtitle:
        subtitle_y = y
        y += _pt_to_in(theme.subtitle_fontsize) * LINE_SPACING
    if has_title or has_subtitle:
        y += GAP_AFTER_TEXT_BLOCK

    legend_top_offset = None  # top of the legend block, from figure top
    if legend is not None and legend.location == "top":
        legend_top_offset = y
        y += legend.block_height + GAP_LEGEND_TO_MAP
    header = y

    # footer stack: distance from figure bottom to the bottom of the map
    y = bottom
    footer_text_y = None
    if has_source or has_credit:
        footer_text_y = y
        y += _pt_to_in(theme.source_fontsize) * LINE_SPACING
    legend_bottom_offset = None  # bottom of the legend block, from figure bottom
    if legend is not None and legend.location == "bottom":
        y += GAP_MAP_TO_FOOTER
        legend_bottom_offset = y
        y += legend.block_height
    y += GAP_MAP_TO_FOOTER
    footer = y

    # map sized from data aspect, capped so slivers don't blow up the canvas
    map_w = content_w
    map_h = map_w / map_aspect
    cap = max_height if max_height is not None else width * DEFAULT_MAX_HEIGHT_RATIO
    max_map_h = cap - header - footer
    if map_h > max_map_h:
        map_h = max(max_map_h, MIN_MAP_HEIGHT)
        map_w = map_h * map_aspect
    map_x = left + (content_w - map_w) / 2.0

    fig_w = width
    fig_h = header + map_h + footer

    def xf(x_in: float) -> float:
        return x_in / fig_w

    def yf_from_top(y_in: float) -> float:
        return 1.0 - y_in / fig_h

    map_rect = (xf(map_x), footer / fig_h, map_w / fig_w, map_h / fig_h)

    legend_rect = None
    if legend is not None:
        bar_w = min(LEGEND_MAX_WIDTH, content_w)
        if legend.align == "left":
            bar_x = left
        else:
            bar_x = left + (content_w - bar_w) / 2.0
        if legend.location == "top":
            bar_top = legend_top_offset + legend.title_space
            bar_y_frac = yf_from_top(bar_top + LEGEND_BAR_HEIGHT)
        else:
            bar_bottom = legend_bottom_offset + legend.tick_space
            bar_y_frac = bar_bottom / fig_h
        legend_rect = (xf(bar_x), bar_y_frac, bar_w / fig_w, LEGEND_BAR_HEIGHT / fig_h)

    title_pos = (xf(left), yf_from_top(title_y)) if title_y is not None else None
    subtitle_pos = (xf(left), yf_from_top(subtitle_y)) if subtitle_y is not None else None
    source_pos = (xf(left), footer_text_y / fig_h) if (has_source and footer_text_y is not None) else None
    credit_pos = (1 - xf(right), footer_text_y / fig_h) if (has_credit and footer_text_y is not None) else None

    return ComputedLayout(
        fig_width=fig_w,
        fig_height=fig_h,
        map_rect=map_rect,
        legend_rect=legend_rect,
        title_pos=title_pos,
        subtitle_pos=subtitle_pos,
        source_pos=source_pos,
        credit_pos=credit_pos,
    )
