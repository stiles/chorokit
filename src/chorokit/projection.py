from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import geopandas as gpd
from pyproj import CRS


@dataclass(frozen=True)
class Projection:
    """Common CRS helpers.

    Methods return pyproj.CRS instances.
    """

    @staticmethod
    def us_albers() -> CRS:
        """CONUS Albers Equal Area (EPSG:5070)."""
        return CRS.from_epsg(5070)


def _is_conus_bounds(minx: float, miny: float, maxx: float, maxy: float) -> bool:
    """Heuristic to detect if data roughly sits in/around the US extent.

    Relaxed to include datasets that extend into Alaska/Hawaii bounds.
    """
    return (minx >= -180 and maxx <= -50) and (miny >= 10 and maxy <= 75)


def _midpoint_lonlat(minx: float, miny: float, maxx: float, maxy: float) -> tuple[float, float]:
    return (minx + maxx) / 2.0, (miny + maxy) / 2.0


def _utm_crs_for_bounds(minx: float, miny: float, maxx: float, maxy: float) -> CRS:
    """Return a UTM CRS based on the geographic midpoint of bounds.

    Uses WGS84 UTM (EPSG:326xx/327xx). Good default for local/regional maps.
    """
    lon = (minx + maxx) / 2.0
    lat = (miny + maxy) / 2.0
    # UTM zone calculation: 1..60
    zone = int((lon + 180) // 6) + 1
    base = 326 if lat >= 0 else 327
    epsg = base * 100 + zone
    return CRS.from_epsg(epsg)


def auto_project(gdf: gpd.GeoDataFrame, fallback: Optional[CRS] = None) -> gpd.GeoDataFrame:
    """Project geographic CRS to a reasonable projected CRS when possible.

    Rules:
    - If CRS is missing, return as-is
    - If CRS is geographic and bounds look like CONUS and are "large", use US Albers (EPSG:5070)
    - If CRS is geographic and bounds are "local/regional", use UTM zone by centroid
    - Else if a fallback is provided, project to fallback
    - Otherwise, return as-is
    """
    if gdf.crs is None:
        return gdf

    crs = CRS.from_user_input(gdf.crs)
    if crs.is_geographic:
        minx, miny, maxx, maxy = gdf.total_bounds
        width_deg = abs(maxx - minx)
        height_deg = abs(maxy - miny)
        largest_span = max(width_deg, height_deg)
        mid_lon, mid_lat = _midpoint_lonlat(minx, miny, maxx, maxy)

        # Large US extents → Albers; small extents → UTM
        if (largest_span >= 8.0) and (
            _is_conus_bounds(minx, miny, maxx, maxy) or (-170 <= mid_lon <= -50 and 10 <= mid_lat <= 75)
        ):
            return gdf.to_crs(Projection.us_albers())
        if largest_span < 8.0:
            utm = _utm_crs_for_bounds(minx, miny, maxx, maxy)
            return gdf.to_crs(utm)
        if fallback is not None:
            return gdf.to_crs(fallback)

    return gdf


def ensure_projected(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a projected GeoDataFrame, trying sensible fallbacks.

    Order:
    1) auto_project rules (CONUS→5070; local→UTM)
    2) if still geographic or missing CRS, try EPSG:3857
    3) if that fails, return input as-is
    """
    try:
        # Heuristic: if CRS says geographic but bounds exceed degree ranges,
        # treat data as already in meters (likely Web Mercator) and set CRS without transforming.
        if gdf.crs is not None and CRS.from_user_input(gdf.crs).is_geographic:
            minx, miny, maxx, maxy = gdf.total_bounds
            if abs(maxx) > 180 or abs(maxy) > 90:
                guessed = 3857  # best-effort guess
                gdf = gdf.set_crs(guessed, allow_override=True)

        projected = auto_project(gdf)
        crs = projected.crs
        if crs is None or CRS.from_user_input(crs).is_geographic:
            return gdf.to_crs(3857)
        return projected
    except Exception:
        try:
            return gdf.to_crs(3857)
        except Exception:
            return gdf


