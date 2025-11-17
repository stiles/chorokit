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

## Palettes ✅ COMPLETED

- ✅ Support ColorBrewer palette names and break counts (seq/div/qual)
  - ✅ Ship complete ColorBrewer 2.0 palette data (35 palettes total)
  - ✅ Sequential: Blues, BuGn, BuPu, GnBu, Greens, Greys, Oranges, OrRd, PuBu, PuBuGn, PuRd, Purples, Reds, YlGn, YlGnBu, YlOrBr, YlOrRd
  - ✅ Diverging: BrBG, PiYG, PRGn, PuOr, RdBu, RdGy, RdYlBu, RdYlGn, Spectral
  - ✅ Qualitative: Accent, Dark2, Paired, Pastel1, Pastel2, Set1, Set2, Set3
  - ✅ API: `LegendConfig(palette=("Blues", 7))` with 3-12 color classes
  - ✅ Proper attribution to Cynthia Brewer, Mark Harrower, Penn State
  - ✅ CLI support: `--palette Blues:7`
  - ✅ Real-world demo with US Census data

## Classification

- Add `scheme="natural"|"equal"|"quantiles"` to CLI and Python API (done)
- Consider additional classifiers: JenksCaspall, MaximumBreaks, StdMean
- Add guardrails: coerce `k` to available palette break counts when `palette` is provided
- Make Jenks (FisherJenks) the default when value distribution is skewed; fall back to quantiles otherwise

## Legend controls

- Expose fine-grained spacing controls in config:
  - `legend_gap_top`, `legend_height_frac`, `legend_width_frac_top`, `legend_top_offset`
- Option for small ticks and no outline (ultra-subtle)
- Support unit annotations on the right of the legend ramp

## Projection

- Add more named projections in `Projection` (Alaska, Hawaii, Europe)
- Auto-detect world vs regional extents; select projection accordingly
- Optional insets (AK/HI) for national maps with layout helpers
- Add US inset layout helper: AK and HI small multiples with configurable positions

## Layout

- Built-in "headline layout" presets: `layout_preset="news"|"technical"` that tune margins, font sizes, legend placement
- Smart margins that adapt to presence/absence of subtitle and credit

## Examples

- US states demo using ACS data with top legend (Reds)
- County-level example with natural breaks and 7-bin ColorBrewer palette
- National choropleth with AK/HI insets and binned Reds palette

## Docs

- Expand README with before/after visuals, CLI walkthrough
- Add a gallery of outputs with code links

## Internal

- Add tests for `compute_breaks`, discrete colormap sizing, and legend rect math
- Type annotations and docstrings for public functions
- Consider a `FigureBuilder` internal object to centralize layout math


