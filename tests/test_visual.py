"""Image-comparison tests across geography shapes, legends and text variants.

Baselines live in tests/baseline. Prefer regenerating them on Linux (the CI OS):

    gh workflow run "update mpl baselines"
    # then download the mpl-baselines artifact into tests/baseline/

Or locally (may differ from CI FreeType):

    .venv/bin/pytest tests/test_visual.py --mpl-generate-path=tests/baseline
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from chorokit import plot_choropleth, LegendConfig, LayoutConfig
from chorokit.style import Theme

# DejaVu Sans ships with matplotlib, so baselines match across machines.
TEST_THEME = Theme(font_family="DejaVu Sans")

FULL_TEXT = dict(
    title="Example headline for the map",
    subtitle="A subtitle with supporting context, 2020",
    source="Source: synthetic test data",
    credit="Chorokit tests",
)

# macOS vs Linux FreeType rasterization often lands around RMS 10–18.
# Keep this high enough for CI until baselines are regenerated on Ubuntu.
TOLERANCE = 25


def _layout(**text) -> LayoutConfig:
    return LayoutConfig(theme=TEST_THEME, **text)


def _plot(gdf, legend, layout):
    fig, _ = plot_choropleth(gdf, value="value", legend=legend, layout=layout)
    return fig


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


GEOS = ["wide", "tall", "square"]


@pytest.fixture
def geo(request, wide_gdf, tall_gdf, square_gdf):
    return {"wide": wide_gdf, "tall": tall_gdf, "square": square_gdf}[request.param]


@pytest.mark.parametrize("geo", GEOS, indirect=True)
@pytest.mark.mpl_image_compare(tolerance=TOLERANCE)
def test_top_legend_scheme_full_text(geo):
    legend = LegendConfig(kind="binned", scheme="quantiles", k=5, title="Value per unit", location="top")
    return _plot(geo, legend, _layout(**FULL_TEXT))


@pytest.mark.parametrize("geo", GEOS, indirect=True)
@pytest.mark.mpl_image_compare(tolerance=TOLERANCE)
def test_bottom_legend_breaks_title_only(geo):
    legend = LegendConfig(
        kind="binned",
        breaks=[0, 10, 25, 50, 100, 400],
        labels=["0", "10", "25", "50", "100", "400"],
        title="Value per unit",
        location="bottom",
    )
    return _plot(geo, legend, _layout(title="Example headline for the map"))


@pytest.mark.parametrize("geo", GEOS, indirect=True)
@pytest.mark.mpl_image_compare(tolerance=TOLERANCE)
def test_no_legend_no_text(geo):
    return _plot(geo, LegendConfig(), _layout())


@pytest.mark.parametrize("geo", GEOS, indirect=True)
@pytest.mark.mpl_image_compare(tolerance=TOLERANCE)
def test_palette_natural_top(geo):
    legend = LegendConfig(kind="binned", palette=("Blues", 7), scheme="natural", title="Value per unit", location="top")
    return _plot(geo, legend, _layout(**FULL_TEXT))


@pytest.mark.parametrize("geo", GEOS, indirect=True)
@pytest.mark.mpl_image_compare(tolerance=TOLERANCE)
def test_continuous_bottom(geo):
    legend = LegendConfig(kind="continuous", vmin=0, vmax=400, title="Value per unit", location="bottom")
    return _plot(geo, legend, _layout(**FULL_TEXT))
