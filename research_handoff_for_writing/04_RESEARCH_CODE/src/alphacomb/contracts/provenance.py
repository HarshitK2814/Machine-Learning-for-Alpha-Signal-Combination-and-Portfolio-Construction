"""Resolve a country's artefacts without trusting modification time.

``outputs/weights/<strategy>/`` and ``outputs/predictions/<strategy>/`` are shared across
countries, and ``paths.latest_run`` returns whichever file was written most recently. So once a
second country has run a stage, "the latest artefact" for a cell silently means that other
country's, and nothing in the path says otherwise. Every consumer that reads per-strategy
artefacts for a *named* country is exposed to this, and three separate tools were caught by it in
one night - a Germany exhibit resolving to India's book, an information-coefficient diagnostic
comparing Japan's scores against India's targets, and a book-characteristics table printing India's
leverage under a German heading.

The fix is that a country run records its own run ids (``pipelines/04_construct_portfolios.py``
writes ``outputs/weights_index/<COUNTRY>_<aum>.csv``) and consumers resolve through that index and
**refuse to fall back**. Failing loudly is the point: a wrong-country weights file produces a
plausible number with no visible symptom, which is the worst kind of error to have available.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import paths


class MissingProvenance(RuntimeError):
    """Raised when a country's artefacts cannot be identified without guessing."""


def weights_index_path(country: str, aum: str = "1e9") -> Path:
    return paths.outputs_root() / "weights_index" / f"{country}_{aum}.csv"


def country_weights(country: str, aum: str = "1e9", *,
                    strategies: list[str] | None = None) -> dict[str, Path]:
    """Map strategy -> weights file for ``country``, from that run's own index.

    ``strategies`` restricts and validates the result; omit it to take everything the index names.
    Raises :class:`MissingProvenance` rather than falling back to modification time.
    """
    index = weights_index_path(country, aum)
    if not index.exists():
        raise MissingProvenance(
            f"no weights index at {index}. Weights are not country-tagged on disk, so the country "
            f"a file belongs to cannot be recovered from its path, and resolving by modification "
            f"time would silently return whichever country ran stage 04 last. Re-run stage 04 for "
            f"{country} (it writes the index), or rebuild one from that run's log with "
            f"tools/weights_index.py.")
    frame = pd.read_csv(index)
    found = dict(zip(frame["strategy"].astype(str), frame["weights"].astype(str)))
    wanted = strategies if strategies is not None else sorted(found)
    missing = [s for s in wanted if s not in found]
    if missing:
        raise MissingProvenance(f"{index} does not cover {', '.join(missing)}")
    out: dict[str, Path] = {}
    for strategy in wanted:
        path = Path(found[strategy])
        if not path.exists():
            raise MissingProvenance(
                f"{index} names a weights file for {strategy} that does not exist: {path}")
        out[strategy] = path
    return out


def country_cells(country: str, aum: str = "1e9") -> dict[str, Path]:
    """Just the factorial cells, which is what most exhibits want."""
    return {k: v for k, v in country_weights(country, aum).items() if k.startswith("cell_")}


def country_source_artefacts(country: str, aum: str = "1e9") -> dict[str, str]:
    """Map strategy -> the stage-02 artefact that country's portfolios consumed.

    Taken from the portfolio manifest for the run ids the index names, so it identifies the scores
    or proposals actually used rather than whatever currently sits newest in the directory.
    """
    index = weights_index_path(country, aum)
    if not index.exists():
        raise MissingProvenance(f"no weights index at {index}")
    manifest = paths.outputs_root() / "manifest_portfolios.csv"
    if not manifest.exists():
        raise MissingProvenance(f"no portfolio manifest at {manifest}")
    want = set(pd.read_csv(index)["run_id"].astype(str))
    rows = pd.read_csv(manifest)
    rows = rows[rows["run_id"].astype(str).isin(want)]
    if rows.empty:
        raise MissingProvenance(
            f"{manifest} has no rows for the run ids in {index.name}; the manifest may have been "
            f"rotated since that run")
    return dict(zip(rows["strategy"].astype(str), rows["source_artefact"].astype(str)))
