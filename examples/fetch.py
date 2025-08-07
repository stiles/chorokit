# -*- coding: utf-8 -*-
from pathlib import Path

import ezesri
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patheffects as path_effects

# prefer roboto but don't die if it's missing
plt.rcParams["font.family"] = "Roboto, DejaVu Sans, Arial"

# ---- inputs / outputs ----
DATA_DIR = Path("./data/processed")
VIS_DIR = Path("./visuals")
DATA_DIR.mkdir(parents=True, exist_ok=True)
VIS_DIR.mkdir(parents=True, exist_ok=True)

la_hoods_url = "https://stilesdata.com/gis/la_city_hoods_county_munis.geojson"
blocks_url = "https://services.arcgis.com/RmCCgQtiZLDCtblq/ArcGIS/rest/services/Census_2020_SRR/FeatureServer/5"

# ---- config ----
variable_config = {
    "pc_nh_wht": {
        "title": "Percent non-Hispanic white",
        "label": "Percent non-Hispanic white population",
        "colors": ["#f7fcf0", "#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4"],
        "breaks": [0, 10, 25, 50, 75, 100],
        "neighborhoods": ["Beverly Hills", "Manhattan Beach", "Santa Monica", "Redondo Beach"],
    },
    "pc_nh_blk": {
        "title": "Percent non-Hispanic Black",
        "label": "Percent non-Hispanic Black population",
        "colors": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a"],
        "breaks": [0, 5, 15, 30, 50, 85],
        "neighborhoods": ["Compton", "Inglewood", "Carson", "Ladera Heights"],
    },
    "pc_nh_asn": {
        "title": "Percent non-Hispanic Asian",
        "label": "Percent non-Hispanic Asian population",
        "colors": ["#f7fcfd", "#e5f5f9", "#ccece6", "#99d8c9", "#66c2a4"],
        "breaks": [0, 5, 15, 30, 50, 90],
        "neighborhoods": ["Monterey Park", "Alhambra", "Arcadia", "Rowland Heights"],
    },
    "pc_hispanic": {
        "title": "Percent Hispanic or Latino",
        "label": "Percent Hispanic or Latino population",
        "colors": ["#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8"],
        "breaks": [0, 20, 40, 60, 80, 100],
        "neighborhoods": ["Boyle Heights", "Huntington Park"],
    },
    "pc_lessthan_hs": {
        "title": "Percent without high school diploma",
        "label": "Percent without high school diploma",
        "colors": ["#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c"],
        "breaks": [0, 10, 20, 30, 40, 100],
        "neighborhoods": ["Huntington Park"],
    },
    "pc_eng_below": {
        "title": "Percent with limited English proficiency",
        "label": "Percent with limited English proficiency",
        "colors": ["#f7f4f9", "#e7e1ef", "#d4b9da", "#c994c7", "#df65b0"],
        "breaks": [0, 10, 20, 30, 40, 80],
        "neighborhoods": ["Koreatown", "Monterey Park", "Alhambra"],
    },
    "med_hh_incm": {
        "title": "Median household income",
        "label": "Median household income ($)",
        "colors": ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476"],
        "breaks": [0, 50_000, 75_000, 100_000, 150_000, 250_000],
        "neighborhoods": ["Beverly Hills", "Manhattan Beach", "Palos Verdes Estates", "Malibu"],
    },
    "pov100rate20": {
        "title": "Population below poverty line rate",
        "label": "Population below poverty line rate",
        "colors": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a"],
        "breaks": [0, 10, 20, 30, 50, 100],
        "neighborhoods": ["Watts", "Westlake", "Pico-Union", "MacArthur Park"],
    },
}

# ---- helpers ----
def load_blocks(url: str, cache_path: Path) -> gpd.GeoDataFrame:
    """Pull once with ezesri, cache locally as GeoJSON for repeat runs."""
    if cache_path.exists():
        gdf = gpd.read_file(cache_path)
    else:
        meta = ezesri.get_metadata(url)  # noqa: F841  # keep around if you want fields
        gdf = ezesri.extract_layer(url)
        gdf.columns = gdf.columns.str.lower()
        gdf.to_file(cache_path, driver="GeoJSON")
    return gdf

def prep_hoods(url: str) -> gpd.GeoDataFrame:
    """Read hoods, drop Catalina/Avalon, add label points inside polygons."""
    hoods = gpd.read_file(url)
    hoods = hoods.query('~name.str.contains("Catalina|Avalon")').copy()
    # representative_point() stays within geometry, better than centroid for labels
    hoods["label_pt"] = hoods.geometry.representative_point()
    return hoods

def build_cmap_and_norm(colors, breaks):
    """Gray for no-data first, then provided colors; include -999 in boundaries."""
    cmap = ListedColormap(["#f0f0f0"] + list(colors))
    boundaries = [-999] + list(breaks)
    norm = BoundaryNorm(boundaries, cmap.N)
    return cmap, norm, boundaries

def format_tick_labels(breaks, is_income: bool):
    base = [f"${int(b):,}" if is_income else f"{int(b)}%" for b in breaks]
    return ["No residents"] + base, [-999] + list(breaks)

def print_top_areas(gdf: gpd.GeoDataFrame, col: str, title: str):
    """Quick stdout summary for the top 5, skip NaNs."""
    s = gdf[col].dropna()
    if s.empty:
        print(f"{title}: No valid data\n")
        return
    top = gdf.loc[s.nlargest(5).index, ["ct20", col]]
    print(f"{title}:")
    for _, r in top.iterrows():
        if col == "med_hh_incm":
            print(f"  Block {r['ct20']}: ${r[col]:,.0f}")
        else:
            print(f"  Block {r['ct20']}: {r[col]:.0f}%")
    print("")

def draw_map(gdf: gpd.GeoDataFrame, hoods: gpd.GeoDataFrame, key: str, cfg: dict):
    """One figure per variable, minimal copies, clear layout."""
    col = key
    # one light transform to add mapped column; do not copy whole frame
    mapped_col = f"{col}__mapped"
    gdf[mapped_col] = gdf[col].fillna(-999)

    cmap, norm, boundaries = build_cmap_and_norm(cfg["colors"], cfg["breaks"])

    fig = plt.figure(figsize=(10, 10), facecolor="white")
    ax = fig.add_axes([0.05, 0.0, 0.9, 0.85])
    ax.axis("off")

    gdf.plot(
        ax=ax,
        column=mapped_col,
        cmap=cmap,
        linewidth=0.05,
        edgecolor="#ffffff",
        legend=False,
        norm=norm,  # explicit norm beats scheme="User_Defined"
    )

    # neighborhood outlines
    hoods.boundary.plot(ax=ax, linewidth=0.4, color="white", alpha=0.8)

    # labels for selected hoods
    key_names = set(cfg.get("neighborhoods", []))
    if key_names:
        hlabs = hoods[hoods["name"].isin(key_names)]
        for _, row in hlabs.iterrows():
            x, y = row["label_pt"].x, row["label_pt"].y
            txt = ax.annotate(
                row["name"],
                xy=(x, y),
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="black",
                alpha=0.7,
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground="white")])

    # set extent once
    xmin, ymin, xmax, ymax = gdf.total_bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    # colorbar
    cbar_ax = fig.add_axes([0.3, 0.90, 0.4, 0.012])
    tick_labels, tick_pos = format_tick_labels(cfg["breaks"], col == "med_hh_incm")
    mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(mappable, cax=cbar_ax, orientation="horizontal", ticks=tick_pos)
    cbar.set_label(cfg["label"], fontsize=10, labelpad=8)
    cbar.ax.set_xticklabels(tick_labels, fontsize=8)
    cbar.ax.tick_params(size=0)
    cbar.outline.set_linewidth(0.5)
    cbar.outline.set_edgecolor("#cccccc")

    out_path = VIS_DIR / f"lacounty_demographics_map_{col}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.05)
    plt.close(fig)

    # cleanup temp column to keep gdf tidy for the next loop
    gdf.drop(columns=[mapped_col], inplace=True)

# ---- pipeline ----
def main():
    # load once, cache locally to avoid hitting the service every run
    blocks_cache = DATA_DIR / "lacounty_demographics_blocks.geojson"
    gdf = load_blocks(blocks_url, blocks_cache)

    # exclude catalina + san clemente (same logic, tighter syntax)
    gdf = gdf.query("~ct20.isin(['599100','599000'])").copy()

    # ensure projected CRS for better label placement if needed; otherwise keep as-is
    # if gdf.crs and gdf.crs.is_geographic:
    #     gdf = gdf.to_crs(3857)

    # hoods with stable label points
    hoods = prep_hoods(la_hoods_url)
    if hoods.crs != gdf.crs:
        hoods = hoods.to_crs(gdf.crs)

    # quick toplines
    print("=== top areas by demographic variable ===\n")
    for key, cfg in variable_config.items():
        if key in gdf.columns:
            print_top_areas(gdf, key, cfg["title"])

    # draw maps
    for key, cfg in variable_config.items():
        if key in gdf.columns:
            draw_map(gdf, hoods, key, cfg)

    # final save once
    out_geo = DATA_DIR / "lacounty_demographics_blocks_processed.geojson"
    gdf.to_file(out_geo, driver="GeoJSON")
    print(f"\nSaved processed blocks → {out_geo}")
    print(f"Maps → {VIS_DIR}")

if __name__ == "__main__":
    main()
