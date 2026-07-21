"""2024 presidential election margin by county.

Reads the pre-built GeoJSON from the presidential-elections repo when present,
otherwise looks for a cached copy under examples/data/raw/. Draws a CONUS
choropleth with a diverging red–blue scale (Republican margin positive).

Usage:
    python examples/election_2024_margin.py
"""

from __future__ import annotations

import geopandas as gpd
import matplotlib.pyplot as plt

from chorokit import Overlay, LayoutConfig, LegendConfig, plot_choropleth
from chorokit.projection import Projection
from chorokit.style import Theme

from _common import ELECTIONS_REPO, OUT, RAW, conus, state_geometries

SOURCE = "Source: MIT Election Data + Science Lab; Dave Leip's Atlas (2024)"
THEME = Theme(title_fontsize=17)

# Signed margin (rep − dem), percentage points. Symmetric breaks around zero.
MARGIN_BREAKS = [-40, -20, -10, -5, 5, 10, 20, 40]
MARGIN_LABELS = ["−40", "−20", "−10", "−5", "5", "10", "20", "40"]


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
    overlay = Overlay(gdf=states, edgecolor="#666666", linewidth=0.4)

    legend = LegendConfig(
        kind="binned",
        breaks=MARGIN_BREAKS,
        labels=MARGIN_LABELS,
        label_style="boundary",
        title="Margin in percentage points (Dem negative, Rep positive)",
        align="left",
        location="top",
        show_missing=True,
    )
    layout = LayoutConfig(
        title="2024 presidential vote margin by county",
        subtitle="Republican share minus Democratic share",
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
        cmap="RdBu_r",
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
