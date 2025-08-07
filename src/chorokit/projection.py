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
    """Heuristic to detect if data roughly sits in the continental US."""
    return (minx >= -170 and maxx <= -50) and (miny >= 15 and maxy <= 75)


def auto_project(gdf: gpd.GeoDataFrame, fallback: Optional[CRS] = None) -> gpd.GeoDataFrame:
    """Project geographic CRS to a reasonable projected CRS when possible.

    Rules:
    - If CRS is missing, return as-is
    - If CRS is geographic and bounds look like CONUS, use US Albers (EPSG:5070)
    - Else if a fallback is provided, project to fallback
    - Otherwise, return as-is
    """
    if gdf.crs is None:
        return gdf

    crs = CRS.from_user_input(gdf.crs)
    if crs.is_geographic:
        minx, miny, maxx, maxy = gdf.total_bounds
        if _is_conus_bounds(minx, miny, maxx, maxy):
            return gdf.to_crs(Projection.us_albers())
        if fallback is not None:
            return gdf.to_crs(fallback)

    return gdf


