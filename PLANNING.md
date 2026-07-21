# Planning

Improvements and ideas for next iterations. Real maps and examples come first:
features are added when an example needs them, not as a standalone wishlist.

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
  - SVG and PDF output that match the PNG look

- Predictable and reproducible
  - Deterministic classifications and colors when breaks are specified
  - Versioned defaults so outputs remain stable across upgrades
  - Visual regression baselines that pass on CI (Linux) as well as locally

- Accessible and readable
  - Provide color-vision-safe palette options and readable tick labels
  - Avoid tiny text and low-contrast annotations

- Small surface area
  - Dataclasses capture configuration; CLI mirrors the Python API
  - Keep the public API compact and stable; add power through focused options

- Composable design
  - Separate modules for projection, legend and layout so advanced users can swap parts later

## How we prioritize

1. Ship examples people would publish (newsroom, research, agency)
2. Add only the API those examples force (insets, SVG, etc.)
3. Document and polish once the maps prove the look
4. Defer nice-to-haves until an example hits them

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
- Bundled Barlow as the default theme font

## v0.3.0 - Real maps, features they force

Goal: more publishable examples, and only the product features those maps need.
Docs stay thin (README gallery); a full docs site waits for 0.4.

### Example gallery
- National US map that includes Alaska and Hawaii (not CONUS-only)
- One metro or regional map beyond LA County
- One non-US example if suitable data is handy
- README becomes a short visual gallery of the best outputs

### Features pulled by those examples
- US Alaska/Hawaii insets for national maps
- SVG and clean PDF output (exact canvas, no tight-bbox surprises)
- Quality fixes only when an example hits them (legend spacing, overlay edge cases, etc.)

### CI reliability
- Visual baselines regenerated on Ubuntu (see `.github/workflows/update-mpl-baselines.yml`)
- Unit tests on Python 3.10 and 3.12; image tests on 3.12 only
- Image RMS tolerance allows macOS/Linux FreeType differences until baselines are Linux-native

### Out of scope for 0.3
- Full ReadTheDocs site
- World projection catalog
- Layout presets (`news` / `technical`)
- Extra classifiers beyond what examples need

## v0.4.0 - Convince and scale

Goal: make the package discoverable and easier for people who did not write it.

### Docs site
- Gallery-driven docs with the 0.3 maps as the spine
- ColorBrewer guide and CLI walkthroughs
- Short tutorials for common jobs (county choropleth, national with insets, custom breaks)

### Smarter defaults
- Auto-pick Jenks vs quantiles for skewed data
- Palette `k` guardrails (coerce to available ColorBrewer class counts)

### Projections and regions
- Named helpers as examples need them (Europe, world, etc.)
- Better auto-detection for world vs regional extents

### Layout presets
- `news` / `technical` / `academic` distilled from patterns in the example gallery

## Later

### Cartography
- Multi-layer fills (not just boundary overlays)
- Annotation system: labels, callouts, north arrows
- Interactive output with web mapping libraries

### Data
- Optional helpers for common sources (Census, etc.)
- Light data-validation checks before plot

### Performance
- Faster rendering for large GeoDataFrames
- Better error messages and full type annotations
