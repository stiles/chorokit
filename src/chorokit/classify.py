from __future__ import annotations

from typing import List, Sequence, Optional, Tuple, Union

import numpy as np
import pandas as pd
from matplotlib.colors import Colormap, ListedColormap
import mapclassify as mc
from matplotlib import cm

from .palettes import create_colorbrewer_cmap, get_palette_colors


def compute_breaks(values: pd.Series, scheme: str = "quantiles", k: int = 5) -> List[float]:
    """Compute class breaks using mapclassify.

    Returns a list of boundaries of length k+1.
    """
    s = values.dropna().astype(float)
    if s.empty:
        return []
    scheme = scheme.lower()
    if scheme in {"quantile", "quantiles", "q"}:
        classifier = mc.Quantiles(s, k=k)
    elif scheme in {"equal", "equalinterval", "e"}:
        classifier = mc.EqualInterval(s, k=k)
    elif scheme in {"natural", "fisherjenks", "jenks", "fj"}:
        classifier = mc.FisherJenks(s, k=k)
    else:
        raise ValueError(f"Unsupported scheme: {scheme}")
    lower = float(s.min())
    upper = float(s.max())
    # mapclassify returns k-1 upper bounds; build full boundary list
    bounds = [lower] + [float(b) for b in classifier.bins]
    # ensure final upper bound includes max
    if bounds[-1] < upper:
        bounds[-1] = upper
    return bounds


def generate_interval_labels(breaks: Sequence[float]) -> List[str]:
    """Generate simple interval labels like 'a–b'."""
    labels: List[str] = []
    for i in range(len(breaks) - 1):
        a = breaks[i]
        b = breaks[i + 1]
        labels.append(f"{_fmt(a)}–{_fmt(b)}")
    return labels


def _fmt(x: float) -> str:
    # format integers without decimals, otherwise compact
    if abs(x - int(x)) < 1e-9:
        return f"{int(x)}"
    return f"{x:.2g}"


def discrete_cmap(base: Union[str, Colormap], n: int) -> ListedColormap:
    """Return a discretized colormap with n distinct colors.
    
    Args:
        base: Base colormap name or Colormap object. If string, will first
              try ColorBrewer palettes, then fall back to matplotlib colormaps.
        n: Number of discrete colors
        
    Returns:
        ListedColormap with n colors
    """
    # Try ColorBrewer first if base is a string
    if isinstance(base, str):
        # Check if it's a ColorBrewer palette
        cb_cmap = create_colorbrewer_cmap(base, n, as_continuous=False)
        if cb_cmap is not None:
            return cb_cmap
            
        # Fall back to matplotlib colormap
        base_cmap = cm.get_cmap(base)
    else:
        base_cmap = base
        
    # Sample colors from continuous colormap
    colors = base_cmap(np.linspace(0.1, 0.9, n))
    return ListedColormap(colors)


