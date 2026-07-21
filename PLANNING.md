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
  - Publication quality by default: high DPI, exact canvas size, no clipping
  - Consistent spacing, legible labels, subtle legend styling
  - SVG output option

- Predictable and reproducible
  - Deterministic classifications and colors when breaks are specified
  - Versioned defaults so outputs remain stable across upgrades
  - Visual regression baselines catch layout regressions

- Accessible and readable
  - Provide color-vision-safe palette options and readable tick labels
  - Avoid tiny text and low-contrast annotations

- Small surface area
  - Dataclasses capture configuration; CLI mirrors the Python API
  - Keep the public API compact and stable; add power through focused options

- Composable design
  - Separate modules for projection, legend and layout so advanced users can swap parts later

## v0.1.0 completed (2025-11-16)

- ColorBrewer 2.0 palette integration (35 palettes)
- Layout system with top/bottom legends
- `plot_choropleth()` API, auto-classification, CLI

## v0.2.0 completed (2026-07-20)

- Deterministic inches-based layout engine; figure height from map aspect
- Visual regression harness (`pytest-mpl`) + gallery contact sheet
- Classification fixes (dedupe breaks, clamp k, label formatting)
- matplotlib 3.9+ colormap API, CI workflow
- Overlays, left-aligned legend, No-data swatch, log + nice-round breaks,
  compact/`%` labels; Census of Agriculture examples

## v0.3.0 - Documentation and examples

### ReadTheDocs site
- Gallery of examples with real-world data
- Python API tutorials for common use cases
- CLI workflows with sample data
- ColorBrewer guide: visual palette selector and usage notes
- Cartographic guidelines and accessibility tips

### Example gallery
- US demographic mapping at state and county level
- International examples (world, European regions)
- Before/after comparisons vs plain matplotlib

## v0.4.0 - Advanced features

### Enhanced classification
- Additional classifiers: JenksCaspall, MaximumBreaks, StdMean
- Smart defaults: Jenks for skewed data, quantiles otherwise
- Palette guardrails: coerce `k` to available palette break counts

### Projection enhancements
- More named projections: Alaska, Hawaii, Europe, world regions
- Auto-detection for world vs regional extents
- US inset support: Alaska/Hawaii small multiples for national maps

### Advanced legend controls
- Fine-grained spacing knobs on `LegendSpec`
- Ultra-subtle styling: minimal ticks, no outlines
- Unit annotations on legend ramps

## v0.5.0 - Polish and performance

### Layout presets
- Built-in presets: `layout_preset="news"|"technical"|"academic"`
- Adaptive spacing based on content presence

### Performance and quality
- Faster rendering for large datasets
- Better error messages and validation
- Complete type annotations and docstrings

## Future considerations

### Advanced cartography
- Multi-layer support
- Annotation system: labels, callouts, north arrows
- Interactive output with web mapping libraries

### Data integration
- Built-in data sources (Census API, World Bank)
- Data validation and quality checks
