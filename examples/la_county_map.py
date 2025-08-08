from pathlib import Path

import geopandas as gpd

from chorokit import plot_choropleth, LegendConfig, LayoutConfig, Projection


HERE = Path(__file__).parent
DATA = HERE / "data" / "processed" / "lacounty_demographics_blocks.geojson"
OUT = HERE / "visuals" / "lacounty_demographics_map_pc_nh_asn.png"


def main() -> None:
    gdf = gpd.read_file(DATA)

    legend = LegendConfig(
        kind="binned",
        title="Percent of population, by block",
        location="top",
        orientation="horizontal",
        breaks=[0, 5, 15, 30, 50, 90],
        labels=["0", "5", "15", "30", "50", "90"],
    )

    layout = LayoutConfig(
        title="Percent non-Hispanic Asian",
        subtitle="Los Angeles County blocks, 2020",
        source="Source: County of Los Angeles, Census 2020 SRR and Demographic Characteristics",
        figure_size=(10, 10),
        # choose projection via config (overrides auto)
        projection=3857,
    )

    fig, _ = plot_choropleth(
        gdf,
        value="pc_nh_asn",
        cmap="Reds",
        legend=legend,
        layout=layout,
        auto_project_data=True,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()


