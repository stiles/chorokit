"""2024 presidential election margin by county.

Reads the pre-built GeoJSON from the presidential-elections repo when present,
otherwise looks for a cached copy under examples/data/raw/. Draws a CONUS
choropleth with a diverging scale: blue for Democratic margins, red for
Republican (no shared near-white bin across zero).

Usage:
    python examples/election_2024_margin.py
"""

from __future__ import annotations

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from chorokit import Overlay, LayoutConfig, LegendConfig, plot_choropleth
from chorokit.projection import Projection
from chorokit.style import Theme

from _common import ELECTIONS_REPO, OUT, RAW, conus, state_geometries

SOURCE = "Sources: MIT Election Data + Science Lab; Dave Leip's Atlas of U.S. Presidential Elections"
THEME = Theme(title_fontsize=17)

# Signed margin (rep − dem) for classification. Legend shows absolute margins
# so Dem (blue, left of 0) and Rep (red, right of 0) both read as positive.
MARGIN_BREAKS = [-40, -30, -20, -10, -5, 0, 5, 10, 20, 30, 40]
MARGIN_LABELS = ["40", "30", "20", "10", "5", "0", "5", "10", "20", "30", "40"]

# ColorBrewer RdBu ends, skipping the near-white center so close races still read
# as blue (Dem) or red (Rep). Order: strong Dem → weak Dem → weak Rep → strong Rep.
MARGIN_COLORS = [
    "#08519c",
    "#3182bd",
    "#6baed6",
    "#bdd7e7",
    "#eff3ff",  # weak Dem — still clearly blue
    "#fee5d9",  # weak Rep — still clearly red
    "#fcae91",
    "#fb6a4a",
    "#de2d26",
    "#a50f15",
]
CMAP_NAME = "chorokit_election_margin"


def _register_margin_cmap() -> str:
    cmap = ListedColormap(MARGIN_COLORS, name=CMAP_NAME)
    try:
        matplotlib.colormaps.register(cmap, name=CMAP_NAME, force=True)
    except TypeError:
        # older matplotlib: no force= kwarg
        if CMAP_NAME in matplotlib.colormaps:
            return CMAP_NAME
        matplotlib.colormaps.register(cmap, name=CMAP_NAME)
    return CMAP_NAME


def load_election_2024() -> gpd.GeoDataFrame:
    candidates = [
        ELECTIONS_REPO / "data" / "geo" / "presidential_election_2024.geojson",
        RAW / "presidential_election_2024.geojson",
    ]
    for path in candidates:
        if path.exists():
            print(f"loading {path}")
            return gpd.read_file(path)
    raise SystemExit(
        "Missing 2024 election GeoJSON.\n"
        f"  expected: {candidates[0]}\n"
        f"  or cache: {candidates[1]}"
    )


def main() -> None:
    gdf = load_election_2024().copy()
    gdf["fips"] = gdf["fips"].astype(str).str.zfill(5)
    if "margin" not in gdf.columns:
        gdf["margin"] = gdf["rep_pct"] - gdf["dem_pct"]

    geo = conus(gdf)
    states = conus(state_geometries())
    overlay = Overlay(gdf=states, edgecolor="#ffffff", linewidth=0.4)
    cmap = _register_margin_cmap()

    legend = LegendConfig(
        kind="binned",
        breaks=MARGIN_BREAKS,
        labels=MARGIN_LABELS,
        label_style="boundary",
        title="Democratic share   |   Republican share",
        align="left",
        location="top",
        show_missing=True,
    )
    layout = LayoutConfig(
        title="Presidential vote margin by county in 2024",
        subtitle="Percentage share of the vote by party in contiguous United States",
        source=SOURCE,
        width=11.0,
        theme=THEME,
        margins=(0.55, 0.35, 0.35, 0.45),
        projection=Projection.us_albers(),
        auto_project=False,
    )

    fig, _ = plot_choropleth(
        geo,
        value="margin",
        cmap=cmap,
        edgecolor="#ffffff",
        linewidth=0.12,
        legend=legend,
        layout=layout,
        overlays=[overlay],
        auto_project_data=False,
        projection=Projection.us_albers(),
    )

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "election_2024_margin.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
