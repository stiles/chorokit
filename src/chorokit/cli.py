from __future__ import annotations

import argparse

import geopandas as gpd

from .api import plot_choropleth, LayoutConfig, LegendConfig


def main() -> None:
    p = argparse.ArgumentParser(prog="chorokit", description="Make a clean choropleth from a GeoJSON and column")
    p.add_argument("geo", help="Path to GeoJSON or any file supported by GeoPandas")
    p.add_argument("value", help="Column name to visualize")
    p.add_argument("-o", "--output", help="Output image path (png, svg, pdf)")
    p.add_argument("--title", default=None)
    p.add_argument("--subtitle", default=None)
    p.add_argument("--source", default=None)
    p.add_argument("--credit", default=None)
    p.add_argument("--cmap", default="YlOrRd")
    p.add_argument("--legend-title", default=None)
    p.add_argument("--legend-kind", choices=["binned", "continuous"], default="binned")
    p.add_argument("--legend-location", choices=["bottom", "top"], default="top")
    p.add_argument("--legend-orientation", choices=["vertical", "horizontal"], default=None)
    p.add_argument(
        "--legend-breaks",
        help="Comma-separated breaks for binned legend (e.g., 0,10,20,30)",
        default=None,
    )
    p.add_argument(
        "--legend-labels",
        help="Comma-separated labels for binned legend (must align with breaks)",
        default=None,
    )
    p.add_argument("--scheme", help="Auto classification scheme: quantiles, equal, natural", default=None)
    p.add_argument("-k", type=int, default=5, help="Number of classes when using --scheme")
    p.add_argument(
        "--palette",
        help="Palette name and count like Reds:5 or Spectral:7 (overrides cmap, sizes discrete colors)",
        default=None,
    )
    p.add_argument("--vmin", type=float, default=None)
    p.add_argument("--vmax", type=float, default=None)
    p.add_argument("--no-auto-project", action="store_true", help="Do not auto-project data")
    p.add_argument("--projection", help="Target CRS (EPSG code like 5070 or proj string)", default=None)
    p.add_argument(
        "--figsize",
        help="Figure size as width,height in inches (e.g., 10,10)",
        default=None,
    )

    args = p.parse_args()

    gdf = gpd.read_file(args.geo)

    # parse legend breaks/labels
    breaks = None
    labels = None
    if args.legend_breaks:
        breaks = [float(x.strip()) for x in args.legend_breaks.split(",") if x.strip()]
    if args.legend_labels:
        labels = [x.strip() for x in args.legend_labels.split(",") if x.strip()]

    # palette parsing
    palette = None
    if args.palette:
        if ":" in args.palette:
            name, n = args.palette.split(":", 1)
            try:
                palette = (name, int(n))
            except ValueError:
                palette = (name, None)  # ignore invalid count
        else:
            palette = (args.palette, None)

    legend = LegendConfig(
        title=args.legend_title,
        kind=args.legend_kind,
        location=args.legend_location,
        orientation=(args.legend_orientation or "horizontal"),  # Always horizontal for top/bottom
        breaks=breaks,
        labels=labels,
        scheme=args.scheme,
        k=args.k,
        palette=palette,  # type: ignore[arg-type]
        vmin=args.vmin,
        vmax=args.vmax,
    )
    # figure size parsing
    figure_size = None
    if args.figsize:
        try:
            w_str, h_str = [s.strip() for s in args.figsize.split(",", 1)]
            figure_size = (float(w_str), float(h_str))
        except Exception:
            figure_size = None

    layout = LayoutConfig(
        title=args.title,
        subtitle=args.subtitle,
        source=args.source,
        credit=args.credit,
        figure_size=(figure_size if figure_size else (12, 8)),
    )

    fig, _ = plot_choropleth(
        gdf,
        value=args.value,
        cmap=args.cmap,
        legend=legend,
        layout=layout,
        auto_project_data=not args.no_auto_project,
        projection=(int(args.projection) if args.projection and args.projection.isdigit() else args.projection),
    )

    if args.output:
        fig.savefig(args.output, dpi=300, bbox_inches="tight")
    else:
        import matplotlib.pyplot as plt

        plt.show()


if __name__ == "__main__":
    main()
