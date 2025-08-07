from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal

from matplotlib.axes import Axes
from matplotlib.colors import Colormap, BoundaryNorm, Normalize
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


LegendOrientation = Literal["vertical", "horizontal"]
LegendLocation = Literal["right", "bottom", "top"]


@dataclass
class BinnedLegend:
    breaks: List[float]
    labels: Optional[List[str]] = None
    orientation: LegendOrientation = "vertical"


@dataclass
class ContinuousLegend:
    vmin: float
    vmax: float
    orientation: LegendOrientation = "vertical"


def add_binned_colorbar(
    fig: Figure,
    cmap: Colormap,
    breaks: List[float],
    labels: Optional[List[str]],
    orientation: LegendOrientation,
    rect: Tuple[float, float, float, float],
    label: Optional[str] = None,
    *,
    tick_label_size: int = 9,
    tick_color: str = "#333333",
    outline_width: float = 0.6,
    outline_color: str = "#cccccc",
    title_fontsize: int = 10,
    title_fontweight: str = "bold",
) -> None:
    norm = BoundaryNorm(breaks, ncolors=cmap.N, clip=False)
    cax = fig.add_axes(rect)
    mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(mappable, cax=cax, orientation=orientation)
    if labels is not None:
        cbar.set_ticks(breaks)
        cbar.set_ticklabels(labels)
    if label:
        if orientation == "horizontal":
            cbar.ax.set_title(label, fontsize=title_fontsize, fontweight=title_fontweight, pad=6)
        else:
            cbar.set_label(label, fontweight=title_fontweight)
    cbar.ax.tick_params(length=0, labelsize=tick_label_size, colors=tick_color)
    # subtle border
    cbar.outline.set_linewidth(outline_width)
    cbar.outline.set_edgecolor(outline_color)


def add_continuous_colorbar(
    fig: Figure,
    cmap: Colormap,
    vmin: float,
    vmax: float,
    orientation: LegendOrientation,
    rect: Tuple[float, float, float, float],
    label: Optional[str] = None,
    *,
    tick_label_size: int = 9,
    tick_color: str = "#333333",
    outline_width: float = 0.6,
    outline_color: str = "#cccccc",
    title_fontsize: int = 10,
    title_fontweight: str = "bold",
) -> None:
    norm = Normalize(vmin=vmin, vmax=vmax)
    cax = fig.add_axes(rect)
    mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(mappable, cax=cax, orientation=orientation)
    if label:
        if orientation == "horizontal":
            cbar.ax.set_title(label, fontsize=title_fontsize, fontweight=title_fontweight, pad=6)
        else:
            cbar.set_label(label, fontweight=title_fontweight)
    cbar.ax.tick_params(length=0, labelsize=tick_label_size, colors=tick_color)
    cbar.outline.set_linewidth(outline_width)
    cbar.outline.set_edgecolor(outline_color)


def legend_rectangles(
    location: LegendLocation,
    margins: Tuple[float, float, float, float],
    *,
    width_frac_top: Optional[float] = None,
    height_frac: Optional[float] = None,
    top_offset: float = 0.0,
    gap_frac: Optional[float] = None,
) -> tuple:
    """Return (map_rect, legend_rect, enforced_orientation) for a location.

    Location can be right, bottom or top.
    """
    left, right, bottom, top = margins
    if location == "right":
        legend_w, gap = 0.03, 0.02
        map_rect = [left, bottom, 1 - left - right - legend_w - gap, 1 - bottom - top]
        legend_rect = [1 - right - legend_w, bottom + 0.15, legend_w, 1 - bottom - top - 0.3]
        return map_rect, legend_rect, "vertical"
    if location == "bottom":
        legend_h, gap = 0.04, 0.02
        map_rect = [left, bottom + legend_h + gap, 1 - left - right, 1 - (bottom + legend_h + gap) - top]
        legend_rect = [left + 0.2, bottom, 1 - left - right - 0.4, legend_h]
        return map_rect, legend_rect, "horizontal"
    if location == "top":
        # more space under subtitle; allow narrow, shallow legend
        legend_h = height_frac if height_frac is not None else 0.03
        gap = gap_frac if gap_frac is not None else 0.05
        usable_w = 1 - left - right
        max_frac = width_frac_top if width_frac_top is not None else 0.3
        legend_w = min(max_frac, usable_w)
        legend_x = left + (usable_w - legend_w) / 2
        # reserve space: legend height + gap + extra top offset for subtitle
        reserved = legend_h + gap + top_offset
        map_rect = [left, bottom, 1 - left - right, 1 - bottom - top - reserved]
        legend_rect = [legend_x, 1 - top - legend_h - top_offset, legend_w, legend_h]
        return map_rect, legend_rect, "horizontal"
    # default fallthrough
    map_rect = [left, bottom, 1 - left - right, 1 - bottom - top]
    return map_rect, None, None


