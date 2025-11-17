# Changelog

All notable changes to Chorokit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-19

### Added
- 🎨 **Complete ColorBrewer 2.0 integration** with 35 professional palettes
  - Sequential palettes (Blues, Reds, Greens, YlOrRd, etc.) 
  - Diverging palettes (RdBu, Spectral, PiYG, etc.)
  - Qualitative palettes (Set1, Set2, Dark2, etc.)
  - Support for 3-12 discrete color classes per palette
  - Proper attribution to Cynthia Brewer, Mark Harrower, and Penn State

- 🎯 **Professional layout system** with publication-ready spacing
  - Smart spacing hierarchy for title, subtitle, legend, map, and source
  - Top and bottom legend placement (removed awkward right legends)
  - Consistent margins and typography matching modern data visualization standards

- 🗺️ **Auto-projection system** for US geographic data
  - Automatic UTM zone selection for local/regional data
  - EPSG:5070 (Albers Equal Area) for CONUS-wide data
  - Manual projection override support

- 🔧 **Simple but powerful API**
  - Single function: `plot_choropleth(gdf, value="column")`
  - ColorBrewer palettes: `LegendConfig(palette=("Blues", 7))`
  - Auto-classification: `scheme="natural"` (Jenks), `"quantiles"`, `"equal"`
  - Custom breaks and labels support

- 💻 **Command-line interface**
  - `chorokit data.geojson column --palette Blues:7 --scheme natural`
  - All Python API features available via CLI
  - Professional output with single command

### Technical
- Built on GeoPandas, matplotlib, and mapclassify
- Type hints throughout codebase
- Modular design with separate projection, legend, and classification modules
- Comprehensive ColorBrewer palette data embedded

### Examples
- US Census state population demo with real data
- LA County demographic mapping example
- CLI usage examples
- ColorBrewer palette showcase

## [0.0.1] - 2024-11-17

### Added
- Initial project structure
- Basic choropleth plotting functionality
- Legend and layout configuration classes
- Auto-projection for geographic data
