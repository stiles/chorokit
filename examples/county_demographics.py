"""US county demographic choropleths from Esri generation/demo attributes.

Downloads (and caches) usa_counties_demos_generations.geojson on first run,
then draws CONUS maps for millennial share, median household income and
population density.

Usage:
    python examples/county_demographics.py
    python examples/county_demographics.py --only millennial_share
"""

from __future__ import annotations

import argparse

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

from chorokit import Overlay, LayoutConfig, LegendConfig, plot_choropleth
from chorokit.projection import Projection
from chorokit.style import Theme

from _common import DEMOS_URL, OUT, RAW, conus, fetch, state_geometries

SOURCE = "Source: Esri Updated Demographics (generations / current year estimates)"
THEME = Theme(title_fontsize=17)

LAYERS = {
    "millennial_share": {
        "column": "millennial_pct",
        "title": "Millennials as a share of county population",
        "cmap": "YlGnBu",
        "k": 5,
        "log": False,
        "percent": True,
        "compact": False,
        "round_breaks": True,
    },
    "gen_z_share": {
        "column": "gen_z_pct",
        "title": "Gen Z as a share of county population",
        "cmap": "YlGnBu",
        "k": 6,
        "log": False,
        "percent": True,
        "compact": False,
        "round_breaks": True,
    },
    "median_income": {
        "column": "MEDHINC_CY",
        "title": "Median household income by county",
        "cmap": "YlGn",
        "k": 6,
        "log": False,
        "percent": False,
        "compact": True,
        "round_breaks": True,
    },
    "population_density": {
        "column": "POPDENS_CY",
        "title": "Population density by county, people per sq. mile",
        "cmap": "YlOrBr",
        "k": 6,
        "log": True,
        "percent": False,
        "compact": True,
        "round_breaks": True,
    },
}


def load_demos() -> gpd.GeoDataFrame:
    path = fetch(DEMOS_URL, RAW / "usa_counties_demos_generations.geojson")
    gdf = gpd.read_file(path)
    gdf = gdf.rename(columns={"ID": "fips", "NAME": "name", "ST_ABBREV": "st_abbrev"})
    gdf["fips"] = gdf["fips"].astype(str).str.zfill(5)
    # millennial share of total population
    tot = gdf["TOTPOP_CY"].replace(0, np.nan)
    gdf["gen_z_pct"] = (gdf["GENZ_CY"] / tot * 100).round(1)
    gdf["millennial_pct"] = (gdf["MILLENN_CY"] / tot * 100).round(1)
    return gdf.set_crs("EPSG:4326", allow_override=True)


def draw_layer(name: str, spec: dict, counties: gpd.GeoDataFrame, states: gpd.GeoDataFrame) -> None:
    geo = conus(counties)
    overlay = Overlay(gdf=conus(states), edgecolor="#666666", linewidth=0.4)

    legend = LegendConfig(
        kind="binned",
        scheme="natural",
        k=spec["k"],
        log=spec["log"],
        round_breaks=spec.get("round_breaks", True),
        label_style="boundary",
        compact=spec["compact"],
        percent=spec["percent"],
        align="left",
        location="top",
        show_missing=True,
    )
    layout = LayoutConfig(
        title=spec["title"],
        source=SOURCE,
        width=11.0,
        theme=THEME,
        margins=(0.55, 0.35, 0.35, 0.45),
        projection=Projection.us_albers(),
        auto_project=False,
    )

    fig, _ = plot_choropleth(
        geo,
        value=spec["column"],
        cmap=spec["cmap"],
        edgecolor="#ffffff",
        linewidth=0.12,
        legend=legend,
        layout=layout,
        overlays=[overlay],
        auto_project_data=False,
        projection=Projection.us_albers(),
    )

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"demos_{name}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--only", choices=list(LAYERS), default=None)
    args = p.parse_args()

    counties = load_demos()
    states = state_geometries()
    names = [args.only] if args.only else list(LAYERS)
    for name in names:
        draw_layer(name, LAYERS[name], counties, states)


if __name__ == "__main__":
    main()
