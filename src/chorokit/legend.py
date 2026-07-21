from __future__ import annotations

from typing import List, Optional, Tuple

from matplotlib.colors import Colormap, BoundaryNorm, Normalize
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


def add_binned_colorbar(
    fig: Figure,
    cmap: Colormap,
    breaks: List[float],
    labels: Optional[List[str]],
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
    """Draw a horizontal binned colorbar into ``rect`` (figure fractions)."""
    norm = BoundaryNorm(breaks, ncolors=cmap.N, clip=False)
    cax = fig.add_axes(rect)
    mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(mappable, cax=cax, orientation="horizontal")
    if labels is not None:
        positions = _tick_positions(breaks, labels)
        cbar.set_ticks(positions)
        cbar.set_ticklabels(labels)
    if label:
        cbar.ax.set_title(label, fontsize=title_fontsize, fontweight=title_fontweight, pad=6)
    cbar.ax.tick_params(length=0, labelsize=tick_label_size, colors=tick_color)
    cbar.outline.set_linewidth(outline_width)
    cbar.outline.set_edgecolor(outline_color)


def add_continuous_colorbar(
    fig: Figure,
    cmap: Colormap,
    vmin: float,
    vmax: float,
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
    """Draw a horizontal continuous colorbar into ``rect`` (figure fractions)."""
    norm = Normalize(vmin=vmin, vmax=vmax)
    cax = fig.add_axes(rect)
    mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(mappable, cax=cax, orientation="horizontal")
    if label:
        cbar.ax.set_title(label, fontsize=title_fontsize, fontweight=title_fontweight, pad=6)
    cbar.ax.tick_params(length=0, labelsize=tick_label_size, colors=tick_color)
    cbar.outline.set_linewidth(outline_width)
    cbar.outline.set_edgecolor(outline_color)


def add_missing_swatch(
    fig: Figure,
    legend_rect: Tuple[float, float, float, float],
    *,
    color: str = "#E6E6E6",
    label: str = "No data",
    text_color: str = "#666666",
    fontsize: int = 9,
) -> None:
    """Draw a small 'No data' swatch to the right of the legend bar."""
    x, y, w, h = legend_rect
    fig_w, fig_h = fig.get_size_inches()
    # square swatch matching the bar's physical height
    sw_w = (h * fig_h) / fig_w
    gap = 0.012
    sw_x = x + w + gap
    ax = fig.add_axes([sw_x, y, sw_w, h])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axvspan(0, 1, color=color)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    # label baseline-aligned with the swatch
    fig.text(sw_x + sw_w + 0.006, y + h * 0.15, label, fontsize=fontsize, color=text_color, va="bottom")


def _tick_positions(breaks: List[float], labels: List[str]) -> List[float]:
    """Map label count to tick positions on a binned colorbar."""
    n = len(breaks)
    n_labels = len(labels)
    if n_labels == n - 1:
        # bin midpoints
        return [(breaks[i] + breaks[i + 1]) / 2 for i in range(n - 1)]
    if n_labels == n:
        # every boundary including min/max
        return list(breaks)
    if n_labels == n - 2 and n >= 3:
        # interior boundaries only (ag-census style)
        return list(breaks[1:-1])
    raise ValueError(
        f"labels must have {n} (all boundaries), {n - 1} (bin midpoints), "
        f"or {n - 2} (interior boundaries) entries, got {n_labels}"
    )
