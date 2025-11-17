"""Simple US State Population Demo with ColorBrewer palette.

Shows how to create a clean choropleth map using real Census data
and ColorBrewer color schemes with just a few lines of code.
"""

from pathlib import Path
import geopandas as gpd

from chorokit import plot_choropleth, LegendConfig, LayoutConfig


def main():
    """Create a simple US population map with ColorBrewer Blues palette."""
    
    # Load US Census state data (download with ezesri if needed)
    data_path = Path(__file__).parent / "data" / "us_states.geojson"
    
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        print("Download with: ezesri fetch <census_layer_url> --format geojson --out us_states.geojson")
        return
    
    print("Loading US state population data...")
    gdf = gpd.read_file(data_path)
    gdf = gdf.query("STATE_ABBR != 'AK' and STATE_ABBR != 'HI'").copy()
    
    # Create map with ColorBrewer palette
    legend = LegendConfig(
        kind="binned",
        palette=("Greens", 7),    # 7-class Greens sequential palette
        scheme="natural",        # Natural breaks (Jenks) classification
        title="Population (millions)",
        location="top"
    )
    
    layout = LayoutConfig(
        title="2020 US State Population",
        subtitle="Census data with ColorBrewer greens palette",
        source="Source: U.S. Census Bureau, 2020 Census",
        figure_size=(12, 8)
    )
    
    # Calculate population in millions for readability
    gdf['pop_millions'] = gdf['POPULATION'] / 1_000_000
    
    # Generate the map
    fig, ax = plot_choropleth(
        gdf,
        value="pop_millions",
        legend=legend,
        layout=layout,
        auto_project_data=True  # Auto-project to appropriate US CRS
    )
    
    # Save the map
    output_path = Path(__file__).parent / "visuals" / "us_population_simple.png"
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    
    print(f"✓ Map saved to {output_path}")


if __name__ == "__main__":
    main()
