from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Literal, Union

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.colors import BoundaryNorm, Normalize

from pyproj import CRS
from .projection import auto_project, ensure_projected
from .legend import add_binned_colorbar, add_continuous_colorbar, legend_rectangles
from .style import Theme
from .classify import compute_breaks, generate_interval_labels, discrete_cmap


@dataclass
class LegendConfig:
    kind: Literal["binned", "continuous"] = "binned"
    title: Optional[str] = None
    location: Literal["bottom", "top"] = "top"
    orientation: Literal["vertical", "horizontal"] = "vertical"
    breaks: Optional[List[float]] = None  # for binned
    labels: Optional[List[str]] = None  # for binned
    vmin: Optional[float] = None  # for continuous
    vmax: Optional[float] = None  # for continuous
    # auto-classification (optional)
    scheme: Optional[str] = None  # e.g., "quantiles", "equal", "natural"
    k: int = 5
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
    figure_size: Tuple[float, float] = (12, 8)
    # left, right, bottom, top - professional margins like Google Trends
    margins: Tuple[float, float, float, float] = (0.04, 0.04, 0.04, 0.04)
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
    auto_project_data: bool = True,
    projection: Optional[Union[int, str, CRS]] = None,
    # convenience passthroughs so callers can avoid constructing LayoutConfig
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    source: Optional[str] = None,
    credit: Optional[str] = None,
) -> Tuple[Figure, Axes]:
    """Minimal end-to-end choropleth with clean defaults.

    This first cut focuses on good spacing and text blocks; projection and insets
    will be added next.
    """
    legend = legend or LegendConfig()
    layout = layout or LayoutConfig()
    # apply convenience fields if provided
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

    # figure and axes layout
    fig = plt.figure(figsize=layout.figure_size)
    # apply theme
    if layout.theme:
        layout.theme.apply()
    left, right, bottom, top = layout.margins

    # allocate map and legend rectangles
    has_legend = (
        bool(legend.breaks) or  # explicit breaks provided
        (legend.kind == "continuous" and legend.vmin is not None and legend.vmax is not None) or  # continuous with range
        (legend.kind == "binned" and legend.scheme is not None) or  # binned with auto-classification
        (legend.kind == "binned" and legend.palette is not None)    # binned with palette
    )
    if has_legend:
        # Use shorter, narrower top legend and increase offset from subtitle/headline
        if legend.location == "top":
            map_rect, legend_rect, enforced = legend_rectangles(
                legend.location,
                (left, right, bottom, top),
                width_frac_top=0.35,  
                height_frac=0.025,    
                top_offset=0.05,      # MORE space from subtitle
                gap_frac=0.005,       # Tight to map
            )
        else:
            map_rect, legend_rect, enforced = legend_rectangles(legend.location, (left, right, bottom, top))
        legend_orientation = enforced or legend.orientation
    else:
        map_rect = [left, bottom, 1 - left - right, 1 - bottom - top]
        legend_rect = None
        legend_orientation = legend.orientation

    ax = fig.add_axes(map_rect)
    ax.set_axis_off()

    # colormap and normalization
    colormap = cm.get_cmap(cmap)

    norm: Union[BoundaryNorm, Normalize, None] = None
    breaks_to_use: Optional[List[float]] = legend.breaks
    labels_to_use: Optional[List[str]] = legend.labels

    # auto breaks/labels if requested and not supplied
    if legend.kind == "binned":
        # If palette is provided, set number of colors from palette second value
        palette_name: Optional[str] = None
        palette_n: Optional[int] = None
        if legend.palette is not None:
            palette_name, palette_n = legend.palette

        # Determine breaks when missing
        if breaks_to_use is None:
            if legend.scheme:
                k_classes = palette_n or legend.k
                breaks_to_use = compute_breaks(gdf_plot[value], scheme=legend.scheme, k=k_classes)
            elif palette_n is not None:
                # default to equal intervals sized to palette
                breaks_to_use = compute_breaks(gdf_plot[value], scheme="equal", k=palette_n)
        if breaks_to_use is not None and labels_to_use is None:
            labels_to_use = generate_interval_labels(breaks_to_use)

        # Choose discrete colormap size based on classes
        if palette_n is not None:
            # prefer palette base name if provided
            base_name = palette_name or cmap
            colormap = discrete_cmap(base_name, palette_n)
        elif breaks_to_use is not None:
            colormap = discrete_cmap(colormap, len(breaks_to_use) - 1)

    if legend.kind == "binned" and breaks_to_use:
        norm = BoundaryNorm(breaks_to_use, ncolors=colormap.N, clip=False)
    elif legend.kind == "continuous" and legend.vmin is not None and legend.vmax is not None:
        norm = Normalize(vmin=legend.vmin, vmax=legend.vmax)

    # draw choropleth
    plot_kwargs = dict(
        column=value,
        cmap=colormap,
        edgecolor=edgecolor,
        linewidth=linewidth,
        missing_kwds={"color": missing_color, "label": "No data"},
        legend=False,
    )
    if norm is not None:
        plot_kwargs["norm"] = norm

    # guard against GeoPandas aspect errors by explicitly setting aspect after plot

    gdf_plot.plot(ax=ax, **plot_kwargs)
    try:
        ax.set_aspect("equal")
    except Exception:
        pass

    # legend drawing
    if legend_rect is not None:
        if legend.kind == "binned" and breaks_to_use:
            add_binned_colorbar(
                fig=fig,
                cmap=colormap,
                breaks=breaks_to_use,
                labels=labels_to_use,
                orientation=legend_orientation,  # enforced by layout choice
                rect=legend_rect,
                label=legend.title,
            )
        elif legend.kind == "continuous" and legend.vmin is not None and legend.vmax is not None:
            add_continuous_colorbar(
                fig=fig,
                cmap=colormap,
                vmin=legend.vmin,
                vmax=legend.vmax,
                orientation=legend_orientation,
                rect=legend_rect,
                label=legend.title,
            )

    # Professional layout with proper spacing hierarchy
    _add_layout_text(fig, layout, left, right, bottom, top, legend.location if legend_rect else None)

    return fig, ax


def _add_layout_text(
    fig: Figure, 
    layout: LayoutConfig, 
    left: float, 
    right: float, 
    bottom: float, 
    top: float,
    legend_location: Optional[str] = None
) -> None:
    """Add title, subtitle, source with professional spacing hierarchy."""
    
    # Calculate spacing based on presence of elements and legend location
    current_y = 0.97  # Tighter top margin
    
    # Title spacing
    if layout.title:
        fig.text(left, current_y, layout.title, 
                ha="left", va="top", fontsize=16, weight="bold", color="#000")
        current_y -= 0.035  # Tighter spacing after title
    
    # Subtitle spacing  
    if layout.subtitle:
        fig.text(left, current_y, layout.subtitle, 
                ha="left", va="top", fontsize=11, color="#333")
        current_y -= 0.02   # Much tighter gap after subtitle
    
    # Extra spacing before top legend (if present)
    if legend_location == "top":
        current_y -= 0.05   # MORE space above legend - push it toward map
    
    # Source and credit at bottom with proper spacing from map
    footer_y = bottom + 0.005  # Very tight margin like Google Trends
    
    if layout.source:
        fig.text(left, footer_y, layout.source, 
                ha="left", va="bottom", fontsize=9, color="#666")
    
    if layout.credit:
        fig.text(1 - right, footer_y, layout.credit, 
                ha="right", va="bottom", fontsize=9, color="#666")
