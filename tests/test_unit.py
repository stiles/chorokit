"""Unit tests for classification, labeling, projection and layout."""

from __future__ import annotations

import geopandas as gpd
import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from chorokit.classify import (
    compute_breaks,
    format_value,
    generate_boundary_labels,
    generate_interval_labels,
    nice_round,
)
from chorokit.layout import LegendSpec, compute_layout
from chorokit.projection import Projection, auto_project, ensure_projected
from chorokit.style import Theme


# ---------------------------------------------------------------------------
# compute_breaks
# ---------------------------------------------------------------------------


def test_quantiles_returns_k_plus_one_bounds():
    s = pd.Series(np.linspace(0, 100, 200))
    breaks = compute_breaks(s, scheme="quantiles", k=5)
    assert len(breaks) == 6
    assert breaks[0] == pytest.approx(0.0)
    assert breaks[-1] == pytest.approx(100.0)
    assert breaks == sorted(breaks)


def test_equal_and_natural_schemes():
    s = pd.Series([1, 2, 3, 10, 50, 100, 200])
    equal = compute_breaks(s, scheme="equal", k=4)
    natural = compute_breaks(s, scheme="natural", k=4)
    assert len(equal) == 5
    assert len(natural) >= 2
    assert equal[0] == pytest.approx(1.0)
    assert equal[-1] == pytest.approx(200.0)


def test_breaks_dedupe_flat_quantiles():
    # mostly zeros with a few large values → quantile edges can collide
    s = pd.Series([0.0] * 90 + [1.0, 2.0, 5.0, 10.0, 100.0] * 2)
    breaks = compute_breaks(s, scheme="quantiles", k=5)
    assert breaks == sorted(set(breaks))
    assert len(breaks) >= 2
    assert all(a < b for a, b in zip(breaks, breaks[1:]))


def test_breaks_clamp_k_to_unique_values():
    s = pd.Series([1.0, 1.0, 2.0, 2.0, 3.0, 3.0])
    breaks = compute_breaks(s, scheme="quantiles", k=10)
    # at most one class per unique value
    assert len(breaks) - 1 <= 3
    assert breaks[0] == pytest.approx(1.0)
    assert breaks[-1] == pytest.approx(3.0)


def test_breaks_empty_and_single_value():
    assert compute_breaks(pd.Series([], dtype=float), k=5) == []
    assert compute_breaks(pd.Series([7.0, 7.0, np.nan]), k=5) == [7.0, 7.0]


def test_unsupported_scheme_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        compute_breaks(pd.Series([1.0, 2.0, 3.0]), scheme="bogus")


def test_nice_round_snaps_to_round_numbers():
    assert nice_round(37412) == 40000
    assert nice_round(13542) == 15000
    assert nice_round(0) == 0.0


def test_round_breaks_snaps_interior_edges():
    s = pd.Series(np.concatenate([np.linspace(1, 50, 80), np.linspace(200, 5000, 40)]))
    raw = compute_breaks(s, scheme="natural", k=5)
    rounded = compute_breaks(s, scheme="natural", k=5, round_breaks=True)
    assert rounded[0] == pytest.approx(raw[0])
    assert rounded[-1] == pytest.approx(raw[-1])
    assert all(a < b for a, b in zip(rounded, rounded[1:]))


def test_round_breaks_preserves_classes_on_tight_percent_range():
    # Gen Z–like shares: most values between ~18–27%. Naive nice-rounding
    # used to collapse five Jenks classes into three (20% / 25% only).
    rng = np.random.default_rng(0)
    s = pd.Series(rng.normal(loc=21.5, scale=2.8, size=800).clip(10, 37))
    raw = compute_breaks(s, scheme="natural", k=5, round_breaks=False)
    rounded = compute_breaks(s, scheme="natural", k=5, round_breaks=True)
    assert len(raw) == 6
    # keep at least 4 classes (5 boundaries) after snapping
    assert len(rounded) >= 5
    assert all(a < b for a, b in zip(rounded, rounded[1:]))


def test_log_breaks_spread_across_orders_of_magnitude():
    # values spanning ~1 to 1e6 — log classification should place interior
    # edges across magnitudes rather than clustering near the max
    rng = np.random.default_rng(0)
    s = pd.Series(10 ** rng.uniform(0, 6, size=500))
    breaks = compute_breaks(s, scheme="natural", k=5, log=True, round_breaks=True)
    assert len(breaks) >= 3
    assert breaks[0] < 100
    assert breaks[-1] > 1e4
    ratios = [breaks[i + 1] / breaks[i] for i in range(len(breaks) - 1)]
    assert max(ratios) / min(ratios) < 1e6  # not a single huge jump at the end


# ---------------------------------------------------------------------------
# generate_interval_labels
# ---------------------------------------------------------------------------


def test_labels_integers_with_thousands():
    labels = generate_interval_labels([0, 1200, 3400, 10000])
    assert labels == ["0–1,200", "1,200–3,400", "3,400–10,000"]


def test_labels_consistent_decimals():
    labels = generate_interval_labels([0.12, 0.25, 0.5, 1.0])
    assert labels == ["0.12–0.25", "0.25–0.50", "0.50–1.00"]


def test_labels_short_breaks():
    assert generate_interval_labels([1.0]) == []
    assert generate_interval_labels([]) == []


def test_compact_and_percent_labels():
    assert format_value(1500, compact=True) == "1.5k"
    assert format_value(7_500_000, compact=True) == "7.5M"
    assert format_value(40, percent=True) == "40%"
    assert generate_interval_labels([0, 20, 40, 75], percent=True) == ["0%–20%", "20%–40%", "40%–75%"]
    assert generate_boundary_labels([0, 400, 2000, 6000, 20000, 75000], compact=True) == [
        "400",
        "2k",
        "6k",
        "20k",
    ]


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------


def _gdf(bounds, crs="EPSG:4326"):
    minx, miny, maxx, maxy = bounds
    return gpd.GeoDataFrame({"v": [1]}, geometry=[box(minx, miny, maxx, maxy)], crs=crs)


def test_us_albers_helper():
    assert Projection.us_albers().to_epsg() == 5070


def test_auto_project_conus_uses_albers():
    # large CONUS-like span
    gdf = _gdf((-120, 25, -70, 50))
    out = auto_project(gdf)
    assert out.crs.to_epsg() == 5070


def test_auto_project_local_uses_utm():
    # LA-ish, small span
    gdf = _gdf((-118.5, 33.8, -117.8, 34.3))
    out = auto_project(gdf)
    epsg = out.crs.to_epsg()
    assert epsg is not None and 32600 <= epsg <= 32760


def test_ensure_projected_already_projected():
    gdf = _gdf((-2e6, 1e6, -1e6, 2e6), crs="EPSG:5070")
    out = ensure_projected(gdf)
    assert out.crs.to_epsg() == 5070


# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------


def test_layout_taller_map_when_aspect_narrower():
    theme = Theme()
    wide = compute_layout(1.9, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
                          has_title=True, has_subtitle=True, has_source=True, has_credit=False)
    tall = compute_layout(0.7, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
                          has_title=True, has_subtitle=True, has_source=True, has_credit=False)
    assert tall.fig_height > wide.fig_height
    # both share the same width
    assert wide.fig_width == tall.fig_width == 10


def test_layout_legend_top_reserves_space():
    theme = Theme()
    no_leg = compute_layout(1.0, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
                            has_title=True, has_subtitle=False, has_source=False, has_credit=False)
    with_leg = compute_layout(
        1.0, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
        has_title=True, has_subtitle=False, has_source=False, has_credit=False,
        legend=LegendSpec(location="top", has_title=True),
    )
    assert with_leg.fig_height > no_leg.fig_height
    assert with_leg.legend_rect is not None
    assert no_leg.legend_rect is None
    # legend sits above the map
    assert with_leg.legend_rect[1] + with_leg.legend_rect[3] > with_leg.map_rect[1] + with_leg.map_rect[3]


def test_layout_caps_extreme_aspect():
    theme = Theme()
    # very tall sliver
    layout = compute_layout(0.1, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
                            has_title=False, has_subtitle=False, has_source=False, has_credit=False,
                            max_height=14.0)
    assert layout.fig_height <= 14.0 + 1e-6
    # map is horizontally centered (narrower than content)
    assert layout.map_rect[2] < 0.9


def test_layout_legend_align_left():
    theme = Theme()
    centered = compute_layout(
        1.5, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
        has_title=True, has_subtitle=False, has_source=False, has_credit=False,
        legend=LegendSpec(location="top", has_title=True, align="center"),
    )
    left = compute_layout(
        1.5, width=10, margins=(0.5, 0.5, 0.4, 0.4), theme=theme,
        has_title=True, has_subtitle=False, has_source=False, has_credit=False,
        legend=LegendSpec(location="top", has_title=True, align="left"),
    )
    assert left.legend_rect is not None and centered.legend_rect is not None
    assert left.legend_rect[0] < centered.legend_rect[0]
    assert left.legend_rect[0] == pytest.approx(0.5 / 10)  # left margin / width


def test_barlow_registers_and_applies():
    from chorokit.style import register_barlow

    assert register_barlow() is True
    theme = Theme()
    theme.apply()
    assert "Barlow" in mpl.rcParams["font.family"] or mpl.rcParams["font.family"] == "Barlow"


