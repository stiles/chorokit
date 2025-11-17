# Planning

Shortlist of improvements and ideas to guide next iterations.

## Core principles

- Easy to use
  - The common case works with a single function call or CLI command
  - Clear names, minimal required arguments, sensible defaults

- Defaults first, flexibility when needed
  - Good-looking defaults for projection, legend, spacing and typography
  - Overridable via small, well-scoped configs; explicit parameters always win over auto

- Speed
  - Avoid unnecessary copies and Python loops, prefer vectorized operations
  - Keep rendering fast for large GeoDataFrames; do only the work that changes the output

- Clean, production ready outputs
  - Publication quality by default: high DPI, tight bounding boxes, no clipping
  - Consistent spacing, legible labels, subtle legend styling
  - SVG output option

- Predictable and reproducible
  - Deterministic classifications and colors when breaks are specified
  - Versioned defaults so outputs remain stable across upgrades

- Accessible and readable
  - Provide color-vision-safe palette options and readable tick labels
  - Avoid tiny text and low-contrast annotations

- Small surface area
  - Dataclasses capture configuration; CLI mirrors the Python API
  - Keep the public API compact and stable; add power through focused options

- Composable design
  - Separate modules for projection, legend and layout so advanced users can swap parts later

## v0.1.0 ✅ SHIPPED (2025-11-16)

### Palettes ✅ COMPLETED
- ✅ Complete ColorBrewer 2.0 palette integration (35 palettes)
- ✅ Sequential, diverging, and qualitative color schemes
- ✅ API: `LegendConfig(palette=("Blues", 7))` with 3-12 color classes
- ✅ CLI support: `--palette Blues:7`
- ✅ Proper attribution to Cynthia Brewer, Mark Harrower, Penn State

### Layout System ✅ COMPLETED  
- ✅ Professional spacing hierarchy (title → subtitle → legend → map → source)
- ✅ Top and bottom legend placement (eliminated right legends)
- ✅ Publication-ready typography and margins
- ✅ Auto-projection for US geographic data

### Core API ✅ COMPLETED
- ✅ Single function API: `plot_choropleth()`
- ✅ Auto-classification: natural breaks, quantiles, equal intervals
- ✅ CLI interface mirroring Python API
- ✅ Real-world examples and documentation

## v0.2.0 - Aesthetic Refinements (Next Release)

### Legend improvements
- **Fix legend dimensions**: Default colorbar is too tall and wide - make more subtle
- **Improve legend positioning**: Better spacing and proportions for professional look
- **Legend styling options**: Ultra-subtle borders, custom spacing controls

### Map alignment  
- **Fix narrow map alignment**: Vertical maps (like LA city) should center or left-align, not right-align
- **Smart map positioning**: Auto-detect map aspect ratio and adjust positioning
- **Consistent centering**: Ensure maps are properly centered within their allocated space

### Output formats
- **SVG output support**: `fig.savefig("map.svg")` for scalable graphics
- **PDF output**: High-quality vector output for publications
- **Format optimization**: Ensure clean output across all supported formats

## v0.3.0 - Documentation & Examples

### ReadTheDocs site
- **Comprehensive documentation**: Gallery of examples with real-world data
- **Python API examples**: Step-by-step tutorials for common use cases
- **CLI examples**: Command-line workflows with sample data
- **ColorBrewer guide**: Visual palette selector and usage recommendations
- **Best practices**: Cartographic guidelines and accessibility tips

### Example gallery
- **US demographic mapping**: State and county-level examples
- **International examples**: World maps, European regions, etc.
- **Different data types**: Population, economic, environmental data
- **Before/after comparisons**: Chorokit vs matplotlib output quality

## v0.4.0 - Advanced Features

### Enhanced classification
- **Additional classifiers**: JenksCaspall, MaximumBreaks, StdMean
- **Smart defaults**: Auto-select Jenks for skewed data, quantiles otherwise
- **Palette guardrails**: Coerce `k` to available palette break counts

### Projection enhancements  
- **More named projections**: Alaska, Hawaii, Europe, world regions
- **Auto-detection**: World vs regional extents with appropriate projection selection
- **US inset support**: Alaska/Hawaii small multiples for national maps

### Advanced legend controls
- **Fine-grained spacing**: Expose `legend_gap_top`, `legend_height_frac`, etc.
- **Ultra-subtle styling**: Minimal ticks, no outlines, custom borders
- **Unit annotations**: Support for units on legend ramps

## v0.5.0 - Polish & Performance

### Layout presets
- **Built-in presets**: `layout_preset="news"|"technical"|"academic"` 
- **Smart margins**: Adaptive spacing based on content presence
- **Theme system**: Consistent typography and spacing across use cases

### Performance and quality
- **Optimization**: Faster rendering for large datasets
- **Memory efficiency**: Reduce memory usage for complex geometries  
- **Error handling**: Better error messages and validation

### Testing and reliability
- **Comprehensive tests**: Unit tests for `compute_breaks`, legend math, projections
- **Integration tests**: End-to-end testing with real data
- **Type safety**: Complete type annotations and docstrings
- **CI/CD**: Automated testing and release pipeline

## Future considerations

### Advanced cartography
- **Multi-layer support**: Overlay multiple datasets
- **Annotation system**: Labels, callouts, north arrows
- **Interactive output**: Integration with web mapping libraries

### Data integration  
- **Built-in data sources**: Census API, World Bank, etc.
- **Data validation**: Automatic data quality checks
- **Format support**: Shapefile, KML, other geographic formats


