# Chorokit

Choropleth helper for GeoPandas with defaults for projection, layout and legend.

## Core principles

- **Easy to use:** the common case works with one function call or CLI command
- **Defaults first, flexibility when needed:** well-designed defaults that you can override with small configs; explicit beats auto
- **Speed:** avoid unnecessary copies and Python loops; keep plotting fast for large GeoDataFrames
- **Clean, production ready outputs:** consistent spacing, legible labels, subtle legend; high DPI and tight bounding boxes
- **Predictable and reproducible:** deterministic classifications and colors when breaks are specified; versioned defaults
- **Accessible and readable:** offer color-vision-safe palettes and readable tick labels
- **Small surface area:** dataclasses capture configuration; CLI mirrors the Python API
- **Composable design:** separate modules for projection, legend and layout so parts can be swapped later

## Install

```bash
pip install -e .
```

## Usage

### Basic Python example

```python
import geopandas as gpd
from chorokit import plot_choropleth

gdf = gpd.read_file("data/states.geojson")
fig, ax = plot_choropleth(
    gdf=gdf,
    value="value_column",
    title="headline",
    subtitle="subhead",
    source="Source: dataset",
)
fig.savefig("out.png", dpi=300)
```

### CLI example

```bash
chorokit data/states.geojson value_column --title "headline" --subtitle "subhead" --source "Source: dataset" -o out.png
```

### Auto classification with top legend and projection

```python
from chorokit import plot_choropleth, LegendConfig, LayoutConfig, Projection

legend = LegendConfig(
    kind="binned",
    title="value per 100k residents",
    location="top",
    orientation="horizontal",
    scheme="quantiles",
    k=5,
)

layout = LayoutConfig(title="headline", subtitle="subhead", source="Source: dataset", projection=Projection.us_albers())

fig, ax = plot_choropleth(gdf, value="value_column", cmap="Reds", legend=legend, layout=layout)
```

### Projection override

```python
# pass an EPSG code directly
fig, ax = plot_choropleth(gdf, value="value_column", projection=3857)

# or set in layout config
layout = LayoutConfig(projection="EPSG:3857")
fig, ax = plot_choropleth(gdf, value="value_column", layout=layout)
```

### CLI with classification and top legend

```bash
chorokit data.geojson value_column \
  --scheme quantiles -k 5 \
  --legend-location top --legend-title "value per 100k"
```

### Palette-sized discrete colors

```bash
# 7-class Spectral palette with quantile breaks
chorokit data.geojson value --palette Spectral:7 --scheme quantiles

# 5-class Reds palette with equal-interval breaks
chorokit data.geojson value --palette Reds:5 --scheme equal
```

## Features

- **Projection**: auto-projects geographic CONUS to EPSG:5070; accept explicit CRS via int, EPSG string or `pyproj.CRS`
- **Legend**: top, right or bottom; binned or continuous; auto breaks via `scheme` and `k`; custom labels and title; subtle default styling
- **Theme**: set font family and text sizes via `LayoutConfig.theme`
- **CLI**: flags for projection, legend options, and auto classification

## License

MIT
