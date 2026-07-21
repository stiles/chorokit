"""USDA Census of Agriculture county maps.

Joins the tidy CSVs in examples/data/ag/ to simplified US county boundaries
(downloaded and cached on first run), then draws three CONUS choropleths that
exercise overlays, nice-round / log breaks, compact labels, a left-aligned
legend and an explicit No-data swatch.

Usage:
    python examples/ag_census_maps.py
    python examples/ag_census_maps.py --only farmland_share
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from chorokit import Overlay, LayoutConfig, LegendConfig, plot_choropleth
from chorokit.projection import Projection
from chorokit.style import Theme

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "ag"
RAW = HERE / "data" / "raw"
OUT = HERE / "visuals"

COUNTIES_URL = "http://stilesdata.com/gis/usa_counties_esri_simple.json"
STATES_URL = "https://stilesdata.com/gis/usa_states_esri_simple.json"

SOURCE = "Source: US Census of Agriculture, 2022"
THEME = Theme(title_fontsize=17)

LAYERS = {
    "farmland_share": {
        "csv": "farmland_share.csv",
        "column": "farmland_pct",
        "title": "Farmland as a share of county land area",
        "cmap": "YlGn",
        "k": 5,
        "log": False,
        "percent": True,
        "compact": False,
    },
    "poultry_sold": {
        "csv": "poultry_sold.csv",
        "column": "poultry_sold_total",
        "title": "Poultry sold by county, head per year",
        "cmap": "YlOrBr",
        "k": 6,
        "log": True,
        "percent": False,
        "compact": True,
    },
    "cattle_sold": {
        "csv": "cattle_sold.csv",
        "column": "cattle_sold",
        "title": "Cattle sold by county, head per year",
        "cmap": "PuRd",
        "k": 6,
        "log": True,
        "percent": False,
        "compact": True,
    },
}


def _fetch(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, dest)
    return dest


def county_geometries() -> gpd.GeoDataFrame:
    path = _fetch(COUNTIES_URL, RAW / "usa_counties_esri_simple.json")
    gdf = gpd.read_file(path)
    return gdf[["fips", "name", "state_name", "geometry"]].set_crs("EPSG:4326", allow_override=True)


def state_geometries() -> gpd.GeoDataFrame:
    path = _fetch(STATES_URL, RAW / "usa_states_esri_simple.json")
    gdf = gpd.read_file(path).rename(columns={"STATE_FIPS": "fips", "STATE_NAME": "name"})
    return gdf[["fips", "name", "geometry"]].set_crs("EPSG:4326", allow_override=True)


def conus(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Lower 48 + DC, projected to CONUS Albers."""
    outside = gdf["fips"].astype(str).str[:2].isin(["02", "15", "72"])
    return gdf[~outside].to_crs(Projection.us_albers())


def draw_layer(name: str, spec: dict, counties: gpd.GeoDataFrame, states: gpd.GeoDataFrame) -> Path:
    csv_path = DATA / spec["csv"]
    df = pd.read_csv(csv_path, dtype={"fips": str})
    joined = counties.merge(df.drop(columns=["state", "county"], errors="ignore"), on="fips", how="left")
    geo = conus(joined)
    state_overlay = Overlay(gdf=conus(states), edgecolor="#666666", linewidth=0.4)

    legend = LegendConfig(
        kind="binned",
        scheme="natural",
        k=spec["k"],
        log=spec["log"],
        round_breaks=True,
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
        linewidth=0.15,
        legend=legend,
        layout=layout,
        overlays=[state_overlay],
        auto_project_data=False,
        projection=Projection.us_albers(),
    )

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"ag_{name}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--only", choices=list(LAYERS), default=None, help="Render a single layer")
    args = p.parse_args()

    if not DATA.exists():
        raise SystemExit(f"missing {DATA}; copy the ag-census CSVs there first")

    counties = county_geometries()
    states = state_geometries()

    names = [args.only] if args.only else list(LAYERS)
    for name in names:
        draw_layer(name, LAYERS[name], counties, states)


if __name__ == "__main__":
    main()
