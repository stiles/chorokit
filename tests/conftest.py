"""Shared fixtures for chorokit tests.

Synthetic geographies are seeded grids with irregular boundaries so tests are
deterministic and independent of large data files. Shapes cover the aspect
ratios that stress the layout engine: wide (CONUS-like), tall (LA-County-like)
and square.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

import matplotlib

matplotlib.use("Agg")


def make_grid_gdf(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    nx: int,
    ny: int,
    seed: int = 0,
    drop_frac: float = 0.12,
) -> gpd.GeoDataFrame:
    """Build a seeded grid of cells with a ragged boundary and a value column.

    Values combine a spatial gradient with lognormal noise so classifications
    (quantiles, equal, natural) all produce distinct bins. A few cells are NaN
    to exercise missing-data rendering.
    """
    rng = np.random.default_rng(seed)
    dx = (maxx - minx) / nx
    dy = (maxy - miny) / ny

    geoms = []
    vals = []
    for j in range(ny):
        for i in range(nx):
            # ragged boundary: drop some edge cells
            on_edge = i == 0 or j == 0 or i == nx - 1 or j == ny - 1
            if on_edge and rng.random() < 0.5:
                continue
            if rng.random() < drop_frac:
                continue
            x0 = minx + i * dx
            y0 = miny + j * dy
            geoms.append(box(x0, y0, x0 + dx, y0 + dy))
            gradient = (i / nx + j / ny) / 2.0
            noise = rng.lognormal(mean=0.0, sigma=0.8)
            vals.append(100.0 * gradient * noise)

    vals = np.asarray(vals)
    # a few missing values
    nan_idx = rng.choice(len(vals), size=max(1, len(vals) // 40), replace=False)
    vals[nan_idx] = np.nan

    return gpd.GeoDataFrame({"value": vals}, geometry=geoms, crs="EPSG:4326")


@pytest.fixture(scope="session")
def wide_gdf() -> gpd.GeoDataFrame:
    """CONUS-like extent, roughly 2:1 wide."""
    return make_grid_gdf(-120.0, 30.0, -78.0, 48.0, nx=28, ny=12, seed=1)


@pytest.fixture(scope="session")
def tall_gdf() -> gpd.GeoDataFrame:
    """LA-County-like extent, taller than wide."""
    return make_grid_gdf(-118.9, 32.8, -117.7, 34.9, nx=10, ny=18, seed=2)


@pytest.fixture(scope="session")
def square_gdf() -> gpd.GeoDataFrame:
    """Roughly square regional extent."""
    return make_grid_gdf(-100.0, 35.0, -95.0, 40.0, nx=14, ny=14, seed=3)
