# Changelog

All notable changes to Chorokit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v0.3.0 - Documentation
- ReadTheDocs site with comprehensive examples
- Gallery of real-world use cases
- ColorBrewer palette guide
- CLI workflow tutorials

---

## [0.2.0] - 2026-07-20

### Added
- Deterministic inches-based layout engine (`layout.py`): figure height is derived
  from the projected map's aspect ratio plus fixed-size text and legend bands
- `LayoutConfig.width` replaces `figure_size`; optional `max_height` caps tall maps
- Visual regression suite (`pytest-mpl`) covering wide, tall and square geographies
  across legend and text variants, with committed baselines
- `tools/gallery.py` contact-sheet renderer for eyeballing the full case matrix
- Unit tests for classification, labeling, projection and layout math
- GitHub Actions workflow running the test suite on Python 3.10 and 3.12
- `Overlay` for drawing boundary layers (e.g. state lines) on top of the choropleth
- Legend options: `align` (center/left), `log` classification, `round_breaks`,
  `label_style` (interval/boundary), `compact` and `percent` label formats,
  and an automatic "No data" swatch when the value column has missing values
- USDA Census of Agriculture county-map examples (`examples/ag_census_maps.py`)
- Bundled Barlow typeface as the default theme font (falls back to DejaVu Sans)

### Changed
- Top and bottom legends are always horizontal; `orientation` on `LegendConfig`
  is ignored (kept for compatibility)
- CLI `--width` replaces `--figsize`; saved images use the exact canvas size
  (no `bbox_inches="tight"`)
- Interval labels use thousands separators and shared decimal precision
- Default theme font is Barlow (bundled); falls back to DejaVu Sans

### Fixed
- Map alignment for tall/narrow geographies: map is centered, figure height
  follows the data aspect instead of a fixed canvas
- `compute_breaks` dedupes colliding quantile edges and clamps `k` to the number
  of unique values
- Replaced deprecated `matplotlib.cm.get_cmap` with `matplotlib.colormaps`

### Removed
- Fraction-based `legend_rectangles` helper (layout now owns rectangle math)

---

## [0.1.0] - 2025-11-19

### Added
- ColorBrewer 2.0 integration with 35 palettes (sequential, diverging, qualitative)
- Layout system with title, subtitle, legend, map and source hierarchy
- Auto-projection: UTM for local/regional data, EPSG:5070 for CONUS
- `plot_choropleth()` API with `LegendConfig` and `LayoutConfig`
- CLI (`chorokit` / `ckit`) mirroring the Python API
- LA County demographics and US population examples

## [0.0.1] - 2024-11-17

### Added
- Initial project structure
- Basic choropleth plotting functionality
- Legend and layout configuration classes
- Auto-projection for geographic data
