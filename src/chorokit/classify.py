from __future__ import annotations

import math
from typing import List, Literal, Optional, Sequence, Union

import numpy as np
import pandas as pd
from matplotlib.colors import Colormap, ListedColormap
import mapclassify as mc
import matplotlib

from .palettes import create_colorbrewer_cmap

# Snap Jenks/quantile edges to mantissa * 10^n so legends read cleanly
# (37,412 → 40,000; 13,542 → 15,000).
NICE_MANTISSAS = [1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5]


def nice_round(value: float) -> float:
    """Snap a positive value to the nearest round number, compared in log space."""
    if value <= 0:
        return 0.0
    exp = math.floor(math.log10(value))
    # keep a coarse lattice for standalone snapping (head counts, income, etc.)
    coarse = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5]
    candidates = [m * 10**e for e in (exp, exp + 1) for m in coarse]
    return min(candidates, key=lambda c: abs(math.log10(c / value)))


def _nice_candidates(value: float) -> List[float]:
    """Candidate round numbers near ``value`` (for neighbor-aware snapping)."""
    if value <= 0:
        return [0.0]
    exp = math.floor(math.log10(abs(value)))
    out: List[float] = []
    for e in (exp - 1, exp, exp + 1):
        for m in NICE_MANTISSAS:
            out.append(m * 10**e)
    return out


def _snap_between(value: float, lo: float, hi: float) -> Optional[float]:
    """Snap ``value`` to a nice number strictly inside ``(lo, hi)``.

    Falls back to integer / half-unit steps when the window is narrow so
    percentage-like series (e.g. 18–27%) do not collapse to two bins.
    """
    if not (lo < hi):
        return None
    cands = [c for c in _nice_candidates(value) if lo < c < hi]
    gap = hi - lo
    if gap <= 100:
        step = 1.0 if gap > 5 else 0.5
        x = math.floor(lo / step) * step + step
        while x < hi - 1e-12:
            cands.append(x)
            x += step
    if not cands:
        return None

    def _dist(c: float) -> float:
        if value > 0 and c > 0:
            return abs(math.log10(c / value))
        return abs(c - value)

    return min(cands, key=_dist)


def _round_interior_breaks(bounds: List[float]) -> List[float]:
    """Snap interior edges without dropping classes when the span is tight."""
    if len(bounds) <= 2:
        return list(bounds)
    rounded: List[float] = [bounds[0]]
    for i in range(1, len(bounds) - 1):
        lo = rounded[-1]
        hi = bounds[i + 1]
        snapped = _snap_between(bounds[i], lo, hi)
        if snapped is None:
            continue
        rounded.append(snapped)
    if bounds[-1] > rounded[-1]:
        rounded.append(bounds[-1])
    elif len(rounded) == 1:
        rounded.append(bounds[-1])
    return rounded


def compute_breaks(
    values: pd.Series,
    scheme: str = "quantiles",
    k: int = 5,
    *,
    log: bool = False,
    round_breaks: bool = False,
) -> List[float]:
    """Compute class breaks using mapclassify.

    Returns a list of boundaries of length up to k+1. ``k`` is clamped when
    there are fewer unique values than classes. Duplicate edges (common with
    quantiles on skewed data) are removed so every returned interval is nonempty.

    When ``log`` is True, classification runs on log10 of positive values and
    edges are transformed back — useful for head counts that span orders of
    magnitude. When ``round_breaks`` is True, interior edges are snapped to
    round numbers via :func:`nice_round` (min/max are preserved). Snapping is
    neighbor-aware so a tight percentage range does not collapse five classes
    into two or three.
    """
    s = values.dropna().astype(float)
    if s.empty:
        return []

    if log:
        s = s[s > 0]
        if s.empty:
            return []
        s_work = np.log10(s)
    else:
        s_work = s

    n_unique = int(pd.Series(s_work).nunique())
    if n_unique < 2:
        v = float(s.min()) if not log else float(s.iloc[0])
        return [v, v]

    k = max(1, min(int(k), n_unique))

    scheme = scheme.lower()
    if scheme in {"quantile", "quantiles", "q"}:
        classifier = mc.Quantiles(s_work, k=k)
    elif scheme in {"equal", "equalinterval", "e"}:
        classifier = mc.EqualInterval(s_work, k=k)
    elif scheme in {"natural", "fisherjenks", "jenks", "fj"}:
        classifier = mc.FisherJenks(s_work, k=k)
    else:
        raise ValueError(f"Unsupported scheme: {scheme}")

    lower = float(s.min())
    upper = float(s.max())
    raw_bins = [float(b) for b in classifier.bins]
    if log:
        raw_bins = [10**b for b in raw_bins]

    bounds = [lower] + raw_bins
    if bounds[-1] < upper:
        bounds[-1] = upper
    elif bounds[-1] > upper:
        bounds[-1] = upper

    deduped: List[float] = [bounds[0]]
    for b in bounds[1:]:
        if b > deduped[-1]:
            deduped.append(b)
    if len(deduped) < 2:
        return [lower, upper]

    if round_breaks and len(deduped) > 2:
        deduped = _round_interior_breaks(deduped)

    return deduped


def format_value(x: float, *, compact: bool = False, percent: bool = False) -> str:
    """Format a single break value for legend ticks."""
    if percent:
        # keep integer percents clean; otherwise drop trailing zeros
        if abs(x - round(x)) < 1e-9:
            return f"{int(round(x))}%"
        return f"{x:g}%"
    if compact:
        ax = abs(x)
        if ax >= 1e6:
            return f"{x / 1e6:g}M"
        if ax >= 1e3:
            return f"{x / 1e3:g}k"
        if abs(x - round(x)) < 1e-9:
            return f"{int(round(x))}"
        return f"{x:g}"
    precision = 0 if abs(x - round(x)) < 1e-9 else _decimal_places(x)
    return _fmt(x, precision)


def generate_interval_labels(
    breaks: Sequence[float],
    *,
    compact: bool = False,
    percent: bool = False,
) -> List[str]:
    """Generate interval labels like '1.5k–20k' or '20%–40%'."""
    if len(breaks) < 2:
        return []
    if compact or percent:
        return [
            f"{format_value(breaks[i], compact=compact, percent=percent)}"
            f"–{format_value(breaks[i + 1], compact=compact, percent=percent)}"
            for i in range(len(breaks) - 1)
        ]
    precision = _shared_precision(breaks)
    return [f"{_fmt(breaks[i], precision)}–{_fmt(breaks[i + 1], precision)}" for i in range(len(breaks) - 1)]


def generate_boundary_labels(
    breaks: Sequence[float],
    *,
    compact: bool = False,
    percent: bool = False,
    interior_only: bool = True,
) -> List[str]:
    """Generate labels placed on class boundaries (ag-census style).

    With ``interior_only=True`` (default), only the edges between classes are
    labeled — not the data min/max — matching a ramp that shows break ticks
    between color blocks.
    """
    if len(breaks) < 2:
        return []
    targets: Sequence[float] = breaks[1:-1] if interior_only and len(breaks) > 2 else breaks
    return [format_value(b, compact=compact, percent=percent) for b in targets]


def _decimal_places(x: float) -> int:
    if abs(x - round(x)) < 1e-9:
        return 0
    s = f"{x:.10f}".rstrip("0")
    if "." not in s:
        return 0
    return len(s.split(".", 1)[1])


def _shared_precision(breaks: Sequence[float]) -> int:
    """Pick a decimal precision that distinguishes consecutive breaks."""
    if all(abs(x - round(x)) < 1e-9 for x in breaks):
        return 0
    precision = max((_decimal_places(x) for x in breaks), default=0)
    precision = min(precision, 6)
    for decimals in range(precision, 7):
        rounded = [round(x, decimals) for x in breaks]
        if all(a < b for a, b in zip(rounded, rounded[1:])):
            return decimals
    return 6


def _fmt(x: float, precision: int) -> str:
    if precision == 0:
        return f"{int(round(x)):,}"
    return f"{x:,.{precision}f}"


def discrete_cmap(base: Union[str, Colormap], n: int) -> ListedColormap:
    """Return a discretized colormap with n distinct colors.

    Args:
        base: Base colormap name or Colormap object. If string, will first
              try ColorBrewer palettes, then fall back to matplotlib colormaps.
        n: Number of discrete colors

    Returns:
        ListedColormap with n colors
    """
    if isinstance(base, str):
        cb_cmap = create_colorbrewer_cmap(base, n, as_continuous=False)
        if cb_cmap is not None:
            return cb_cmap
        base_cmap = matplotlib.colormaps[base]
    else:
        base_cmap = base

    colors = base_cmap(np.linspace(0.1, 0.9, n))
    return ListedColormap(colors)
