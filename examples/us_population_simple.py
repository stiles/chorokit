"""Simple US State Population Demo with ColorBrewer palette.

Shows how to create a clean choropleth map using real Census data
and ColorBrewer color schemes with just a few lines of code.
"""

from pathlib import Path
import geopandas as gpd

from chorokit import plot_choropleth, LegendConfig, LayoutConfig


def main():
    """Create a simple US population map with ColorBrewer Blues palette."""

    data_path = Path(__file__).parent / "data" / "us_states.geojson"

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        print("Download with: ezesri fetch <census_layer_url> --format geojson --out us_states.geojson")
        return

    print("Loading US state population data...")
    gdf = gpd.read_file(data_path)
    gdf = gdf.query("STATE_ABBR != 'AK' and STATE_ABBR != 'HI'").copy()

    legend = LegendConfig(
        kind="binned",
        palette=("Greens", 7),
        scheme="natural",
        title="Population (millions)",
        location="top",
    )

    layout = LayoutConfig(
        title="2020 US State Population",
        subtitle="Census data with ColorBrewer greens palette",
        source="Source: U.S. Census Bureau, 2020 Census",
        width=12.0,
    )

    gdf["pop_millions"] = gdf["POPULATION"] / 1_000_000

    fig, ax = plot_choropleth(
        gdf,
        value="pop_millions",
        legend=legend,
        layout=layout,
        auto_project_data=True,
    )

    output_path = Path(__file__).parent / "visuals" / "us_population_simple.png"
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300)

    print(f"Map saved to {output_path}")


if __name__ == "__main__":
    main()
