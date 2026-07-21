"""Shared helpers for chorokit example scripts."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import geopandas as gpd

from chorokit.projection import Projection

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
OUT = HERE / "visuals"

STATES_URL = "https://stilesdata.com/gis/usa_states_esri_simple.json"
DEMOS_URL = "https://stilesdata.com/gis/usa_counties_demos_generations.geojson"

# Local elections repo (optional; examples fall back to cached copies)
ELECTIONS_REPO = Path(__file__).resolve().parents[2] / "presidential-elections"


def fetch(url: str, dest: Path, *, user_agent: str = "chorokit-examples/0.2") -> Path:
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=300) as resp:
        dest.write_bytes(resp.read())
    return dest


def state_geometries() -> gpd.GeoDataFrame:
    path = fetch(STATES_URL, RAW / "usa_states_esri_simple.json")
    gdf = gpd.read_file(path).rename(columns={"STATE_FIPS": "fips", "STATE_NAME": "name"})
    return gdf[["fips", "name", "geometry"]].set_crs("EPSG:4326", allow_override=True)


def conus(gdf: gpd.GeoDataFrame, fips_col: str = "fips") -> gpd.GeoDataFrame:
    """Lower 48 + DC, projected to CONUS Albers.

    Accepts 2-digit state FIPS or 5-digit county FIPS. Zero-padding state
    codes to 5 digits would turn ``"02"`` into ``"00002"`` and break the
    Alaska/Hawaii filter, so we branch on string length.
    """
    fips = gdf[fips_col].astype(str).str.strip()
    # state rows are usually 1–2 digits; county rows are 4–5
    state_prefix = fips.str.zfill(2).where(fips.str.len() <= 2, fips.str.zfill(5).str[:2])
    outside = state_prefix.isin(["02", "15", "72"])
    out = gdf.loc[~outside].copy()
    if out.crs is None:
        out = out.set_crs("EPSG:4326")
    return out.to_crs(Projection.us_albers())
