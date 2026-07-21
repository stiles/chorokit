from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple, Literal, Union

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.colors import BoundaryNorm, Normalize

from pyproj import CRS
from .projection import ensure_projected
from .legend import add_binned_colorbar, add_continuous_colorbar, add_missing_swatch
from .layout import LegendSpec, compute_layout
from .style import Theme
from .classify import (
    compute_breaks,
    discrete_cmap,
    generate_boundary_labels,
    generate_interval_labels,
)


@dataclass
class Overlay:
    """A boundary or outline layer drawn on top of the choropleth."""

    gdf: gpd.GeoDataFrame
    edgecolor: str = "#666666"
    linewidth: float = 0.4
    facecolor: str = "none"
    zorder: int = 3


@dataclass
class LegendConfig:
    kind: Literal["binned", "continuous"] = "binned"
    title: Optional[str] = None
    location: Literal["bottom", "top"] = "top"
    # "center" (default) or "left" under the title block
    align: Literal["center", "left"] = "center"
    # deprecated and ignored: top/bottom legends are always horizontal
    orientation: Optional[str] = None
    breaks: Optional[List[float]] = None  # for binned
    labels: Optional[List[str]] = None  # for binned
    vmin: Optional[float] = None  # for continuous
    vmax: Optional[float] = None  # for continuous
    # auto-classification (optional)
    scheme: Optional[str] = None  # e.g., "quantiles", "equal", "natural"
    k: int = 5
    # classify on log10 of positive values (good for skewed counts)
    log: bool = False
    # snap interior break edges to round numbers
    round_breaks: bool = False
    # "interval" → 'a–b' at bin midpoints; "boundary" → ticks on class edges
    label_style: Literal["interval", "boundary"] = "interval"
    # compact k/M formatting; percent appends '%'
    compact: bool = False
    percent: bool = False
    # show a 'No data' swatch when the value column has missing values
    show_missing: Union[bool, Literal["auto"]] = "auto"
    missing_label: str = "No data"
    # color palette preference for binned legends
    # When provided, we discretize to this many colors. If breaks are not provided,
    # we compute breaks using `scheme` (default to equal intervals) sized to n.
    palette: Optional[Tuple[str, int]] = None


@dataclass
class LayoutConfig:
    title: Optional[str] = None
    subtitle: Optional[str] = None
    source: Optional[str] = None
    credit: Optional[str] = None
    # figure width in inches; height is derived from the map's aspect ratio
    # plus the text and legend bands, so spacing is identical for any geography
    width: float = 10.0
    # optional cap on figure height in inches (default: 1.4 x width)
    max_height: Optional[float] = None
    # left, right, bottom, top margins in inches
    margins: Tuple[float, float, float, float] = (0.5, 0.5, 0.4, 0.4)
    # map projection controls (optional overrides)
    projection: Optional[Union[int, str, CRS]] = None
    auto_project: Optional[bool] = None
    # theme applied to matplotlib rcParams
    theme: Theme = field(default_factory=Theme)


def plot_choropleth(
    gdf: gpd.GeoDataFrame,
    value: str,
    cmap: str = "YlOrRd",
    missing_color: str = "#E6E6E6",
    edgecolor: str = "#FFFFFF",
    linewidth: float = 0.5,
    legend: Optional[LegendConfig] = None,
    layout: Optional[LayoutConfig] = None,
    overlays: Optional[Sequence[Overlay]] = None,
    auto_project_data: bool = True,
    projection: Optional[Union[int, str, CRS]] = None,
    # convenience passthroughs so callers can avoid constructing LayoutConfig
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    source: Optional[str] = None,
    credit: Optional[str] = None,
) -> Tuple[Figure, Axes]:
    """End-to-end choropleth with clean defaults for projection, legend and layout.

    Figure height is derived from the projected data's aspect ratio plus the
    text and legend bands, so spacing is identical for any geography.

    Pass ``overlays`` (e.g. state boundaries) to draw outline layers on top
    of the filled polygons.
    """
    legend = legend or LegendConfig()
    layout = layout or LayoutConfig()
    if title is not None:
        layout.title = title
    if subtitle is not None:
        layout.subtitle = subtitle
    if source is not None:
        layout.source = source
    if credit is not None:
        layout.credit = credit

    # projection (layout overrides if set)
    effective_auto = auto_project_data if layout.auto_project is None else bool(layout.auto_project)
    proj_to_use: Optional[Union[int, str, CRS]] = projection if projection is not None else layout.projection
    if proj_to_use is not None:
        gdf_plot = gdf.to_crs(proj_to_use)
    else:
        gdf_plot = ensure_projected(gdf) if effective_auto else gdf

    target_crs = gdf_plot.crs

    colormap = matplotlib.colormaps[cmap]

    norm: Union[BoundaryNorm, Normalize, None] = None
    breaks_to_use: Optional[List[float]] = legend.breaks
    labels_to_use: Optional[List[str]] = legend.labels

    if legend.kind == "binned":
        palette_name: Optional[str] = None
        palette_n: Optional[int] = None
        if legend.palette is not None:
            palette_name, palette_n = legend.palette

        if breaks_to_use is None:
            if legend.scheme:
                k_classes = palette_n or legend.k
                breaks_to_use = compute_breaks(
                    gdf_plot[value],
                    scheme=legend.scheme,
                    k=k_classes,
                    log=legend.log,
                    round_breaks=legend.round_breaks,
                )
            elif palette_n is not None:
                breaks_to_use = compute_breaks(
                    gdf_plot[value],
                    scheme="equal",
                    k=palette_n,
                    log=legend.log,
                    round_breaks=legend.round_breaks,
                )
        if breaks_to_use is not None and labels_to_use is None:
            if legend.label_style == "boundary":
                labels_to_use = generate_boundary_labels(
                    breaks_to_use, compact=legend.compact, percent=legend.percent
                )
            else:
                labels_to_use = generate_interval_labels(
                    breaks_to_use, compact=legend.compact, percent=legend.percent
                )

        if palette_n is not None:
            base_name = palette_name or cmap
            colormap = discrete_cmap(base_name, palette_n)
        elif breaks_to_use is not None:
            colormap = discrete_cmap(colormap, len(breaks_to_use) - 1)

    if legend.kind == "binned" and breaks_to_use:
        norm = BoundaryNorm(breaks_to_use, ncolors=colormap.N, clip=False)
    elif legend.kind == "continuous" and legend.vmin is not None and legend.vmax is not None:
        norm = Normalize(vmin=legend.vmin, vmax=legend.vmax)

    has_legend = (
        (legend.kind == "binned" and bool(breaks_to_use))
        or (legend.kind == "continuous" and legend.vmin is not None and legend.vmax is not None)
    )
    has_missing = bool(gdf_plot[value].isna().any())
    if legend.show_missing == "auto":
        draw_missing = has_missing and has_legend
    else:
        draw_missing = bool(legend.show_missing) and has_legend

    if layout.theme:
        layout.theme.apply()
    minx, miny, maxx, maxy = gdf_plot.total_bounds
    span_x = float(maxx - minx)
    span_y = float(maxy - miny)
    map_aspect = span_x / span_y if span_x > 0 and span_y > 0 else 1.0

    legend_spec = (
        LegendSpec(location=legend.location, has_title=bool(legend.title), align=legend.align)
        if has_legend
        else None
    )
    computed = compute_layout(
        map_aspect,
        width=layout.width,
        margins=layout.margins,
        theme=layout.theme,
        has_title=bool(layout.title),
        has_subtitle=bool(layout.subtitle),
        has_source=bool(layout.source),
        has_credit=bool(layout.credit),
        legend=legend_spec,
        max_height=layout.max_height,
    )

    fig = plt.figure(figsize=(computed.fig_width, computed.fig_height))
    ax = fig.add_axes(computed.map_rect)
    ax.set_axis_off()
    ax.margins(0)

    plot_kwargs = dict(
        column=value,
        cmap=colormap,
        edgecolor=edgecolor,
        linewidth=linewidth,
        missing_kwds={"color": missing_color, "label": legend.missing_label},
        legend=False,
    )
    if norm is not None:
        plot_kwargs["norm"] = norm

    gdf_plot.plot(ax=ax, **plot_kwargs)
    try:
        ax.set_aspect("equal")
    except Exception:
        pass

    if overlays:
        for overlay in overlays:
            ogdf = overlay.gdf
            if target_crs is not None and ogdf.crs is not None and ogdf.crs != target_crs:
                ogdf = ogdf.to_crs(target_crs)
            elif target_crs is not None and ogdf.crs is None:
                ogdf = ogdf.set_crs(target_crs)
            ogdf.plot(
                ax=ax,
                facecolor=overlay.facecolor,
                edgecolor=overlay.edgecolor,
                linewidth=overlay.linewidth,
                zorder=overlay.zorder,
            )

    if computed.legend_rect is not None:
        if legend.kind == "binned" and breaks_to_use:
            add_binned_colorbar(
                fig=fig,
                cmap=colormap,
                breaks=breaks_to_use,
                labels=labels_to_use,
                rect=computed.legend_rect,
                label=legend.title,
            )
        elif legend.kind == "continuous" and legend.vmin is not None and legend.vmax is not None:
            add_continuous_colorbar(
                fig=fig,
                cmap=colormap,
                vmin=legend.vmin,
                vmax=legend.vmax,
                rect=computed.legend_rect,
                label=legend.title,
            )
        if draw_missing:
            add_missing_swatch(
                fig,
                computed.legend_rect,
                color=missing_color,
                label=legend.missing_label,
                text_color=layout.theme.quiet_color,
            )

    _add_layout_text(fig, layout, computed)

    return fig, ax


def _add_layout_text(fig: Figure, layout: LayoutConfig, computed) -> None:
    """Add title, subtitle, source and credit at layout-computed anchors."""
    theme = layout.theme

    if layout.title and computed.title_pos:
        x, y = computed.title_pos
        fig.text(x, y, layout.title, ha="left", va="top",
                 fontsize=theme.title_fontsize, weight=theme.title_weight, color="#000")

    if layout.subtitle and computed.subtitle_pos:
        x, y = computed.subtitle_pos
        fig.text(x, y, layout.subtitle, ha="left", va="top",
                 fontsize=theme.subtitle_fontsize, color=theme.text_color)

    if layout.source and computed.source_pos:
        x, y = computed.source_pos
        fig.text(x, y, layout.source, ha="left", va="bottom",
                 fontsize=theme.source_fontsize, color=theme.quiet_color)

    if layout.credit and computed.credit_pos:
        x, y = computed.credit_pos
        fig.text(x, y, layout.credit, ha="right", va="bottom",
                 fontsize=theme.source_fontsize, color=theme.quiet_color)
