"""Render a matrix of chorokit maps into a single contact sheet.

Every layout change should be checked against this sheet so a fix for one
geography or legend variant doesn't break another.

Usage:
    python tools/gallery.py [-o examples/visuals/gallery.png] [--include-real-data]
"""

from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import matplotlib

matplotlib.use("Agg")

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from chorokit import plot_choropleth, LegendConfig, LayoutConfig  # noqa: E402
from chorokit.style import Theme  # noqa: E402
from conftest import make_grid_gdf  # noqa: E402


THEME = Theme(font_family="DejaVu Sans")

FULL_TEXT = dict(
    title="Example headline for the map",
    subtitle="A subtitle with supporting context, 2020",
    source="Source: synthetic test data",
    credit="Chorokit",
)


def geographies(include_real_data: bool) -> dict[str, gpd.GeoDataFrame]:
    geos = {
        "wide": make_grid_gdf(-120.0, 30.0, -78.0, 48.0, nx=28, ny=12, seed=1),
        "tall": make_grid_gdf(-118.9, 32.8, -117.7, 34.9, nx=10, ny=18, seed=2),
        "square": make_grid_gdf(-100.0, 35.0, -95.0, 40.0, nx=14, ny=14, seed=3),
    }
    if include_real_data:
        la_path = REPO / "examples" / "data" / "processed" / "lacounty_demographics_blocks.geojson"
        if la_path.exists():
            la = gpd.read_file(la_path).rename(columns={"pc_nh_asn": "value"})
            geos["la_county"] = la
    return geos


@dataclass
class Case:
    name: str
    legend: Callable[[], LegendConfig]
    text: dict


LEGEND_VARIANTS: list[tuple[str, Callable[[], LegendConfig]]] = [
    ("top scheme", lambda: LegendConfig(kind="binned", scheme="quantiles", k=5, title="Value per unit", location="top")),
    ("top palette", lambda: LegendConfig(kind="binned", palette=("Blues", 7), scheme="natural", title="Value per unit", location="top")),
    ("bottom breaks", lambda: LegendConfig(kind="binned", breaks=[0, 10, 25, 50, 100, 400], title="Value per unit", location="bottom")),
    ("bottom continuous", lambda: LegendConfig(kind="continuous", vmin=0, vmax=400, title="Value per unit", location="bottom")),
    ("no legend", lambda: LegendConfig()),
]

TEXT_VARIANTS: list[tuple[str, dict]] = [
    ("full text", FULL_TEXT),
    ("title only", dict(title="Example headline for the map")),
    ("no text", {}),
]


def build_cases() -> list[Case]:
    cases: list[Case] = []
    for legend_name, legend_fn in LEGEND_VARIANTS:
        cases.append(Case(f"{legend_name} / full text", legend_fn, FULL_TEXT))
    # text variants against the default top-scheme legend
    for text_name, text in TEXT_VARIANTS[1:]:
        cases.append(Case(f"top scheme / {text_name}", LEGEND_VARIANTS[0][1], text))
    return cases


def render_panel(gdf: gpd.GeoDataFrame, case: Case) -> "mpimg.np.ndarray":
    layout = LayoutConfig(theme=THEME, **case.text)
    fig, _ = plot_choropleth(gdf, value="value", legend=case.legend(), layout=layout)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=72)
    plt.close(fig)
    buf.seek(0)
    return mpimg.imread(buf)


def main() -> None:
    p = argparse.ArgumentParser(description="Render the chorokit gallery contact sheet")
    p.add_argument("-o", "--output", default=str(REPO / "examples" / "visuals" / "gallery.png"))
    p.add_argument("--include-real-data", action="store_true", help="Also render the LA County example data")
    args = p.parse_args()

    geos = geographies(args.include_real_data)
    cases = build_cases()

    nrows = len(cases)
    ncols = len(geos)
    sheet, axes = plt.subplots(nrows, ncols, figsize=(ncols * 5, nrows * 4))
    if nrows == 1:
        axes = [axes]

    for r, case in enumerate(cases):
        for c, (geo_name, gdf) in enumerate(geos.items()):
            ax = axes[r][c] if ncols > 1 else axes[r]
            try:
                img = render_panel(gdf, case)
                ax.imshow(img)
            except Exception as exc:  # keep rendering the rest of the sheet
                ax.text(0.5, 0.5, f"ERROR:\n{exc}", ha="center", va="center", fontsize=8, color="red", wrap=True)
            ax.set_title(f"{geo_name} | {case.name}", fontsize=9)
            ax.set_axis_off()

    sheet.tight_layout()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.savefig(out, dpi=100)
    print(f"Wrote {out} ({nrows * ncols} panels)")


if __name__ == "__main__":
    main()
