"""Protection against output collisions between differently parameterised or differently tagged runs.

Several research tools write to a path derived only from a short ``--tag``. Two runs that differ in anything else (an AUM
ladder, a weighting scheme, a cost flag) but share a tag, or whose tags normalise to the same directory (``""`` and
``"default"``), silently overwrite one another. This has happened. ``claim_output`` makes that impossible by default.

How it works. Before a run writes ``path`` it calls ``claim_output(path, params)``. A sidecar record
(``<path>.run.json``, or ``<dir>/.run.json`` for a directory) stores a SHA-256 fingerprint of the canonical-JSON ``params``.

* Nothing exists yet: the claim is recorded and the run proceeds.
* A record exists with the **same** fingerprint: the run is a re-run of the same job and proceeds.
* A record exists with a **different** fingerprint: refused (``OutputCollision``).
* The path exists with **no** record (legacy output of unknown origin): refused.
* ``overwrite=True`` replaces the record and proceeds; use it only when the earlier output is to be discarded.

``params`` must include the tag as given, so ``""`` and ``"default"`` differ. Nothing here changes what a run computes.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIDECAR_SUFFIX = ".run.json"


class OutputCollision(RuntimeError):
    """A run would overwrite the output of a different run, or of one with unknown provenance."""


def fingerprint(params: dict[str, Any]) -> str:
    blob = json.dumps(params, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def sidecar_path(path: str | os.PathLike, *, is_dir: bool = False) -> Path:
    p = Path(path)
    return p / ".run.json" if is_dir else p.with_name(p.name + SIDECAR_SUFFIX)


def claim_output(path: str | os.PathLike, params: dict[str, Any], *, is_dir: bool = False,
                 overwrite: bool = False) -> str:
    """Claim ``path`` for the run described by ``params``. Returns the fingerprint. Raises ``OutputCollision``."""
    p = Path(path)
    side = sidecar_path(p, is_dir=is_dir)
    fp = fingerprint(params)
    exists = p.exists() and (any(p.iterdir()) if is_dir else True)
    if side.exists():
        old = json.loads(side.read_text(encoding="utf-8")).get("fingerprint")
        if old != fp and not overwrite:
            raise OutputCollision(
                f"{p} was written by a different run (fingerprint {str(old)[:12]} != {fp[:12]}). "
                "Use a distinct --tag or pass --overwrite to discard the earlier output.")
    elif exists and not overwrite:
        raise OutputCollision(
            f"{p} already exists and has no run record, so its origin is unknown. "
            "Use a distinct --tag or pass --overwrite to discard it.")
    if is_dir:
        p.mkdir(parents=True, exist_ok=True)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
    tmp = side.with_name(side.name + ".tmp")
    tmp.write_text(json.dumps({"fingerprint": fp, "params": params,
                               "claimed_utc": datetime.now(timezone.utc).isoformat()},
                              indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, side)
    return fp


def claim_run(paths, args, *, exclude: tuple[str, ...] = ("overwrite",)) -> str:
    """Claim every path in ``paths`` for the run described by an ``argparse`` namespace.

    The parameters are all parsed arguments except those in ``exclude`` (``--overwrite`` itself by default); ``--overwrite``
    on the namespace is honoured. Convenience wrapper for tools that write a handful of fixed-name files.
    """
    params = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items() if k not in exclude}
    ow = bool(getattr(args, "overwrite", False))
    fp = ""
    for p in paths:
        fp = claim_output(p, params, overwrite=ow)
    return fp


def claim_run_items(items, args, *, exclude: tuple[str, ...] = ("overwrite",)) -> list[str]:
    """Claim several outputs, each with its own parameter fingerprint.

    ``items`` is an iterable of ``(path, overrides)``. A path's parameters are the parsed arguments minus ``exclude`` minus
    the keys in ``overrides``, plus ``overrides`` itself. Use it when one invocation writes several per-item files (for
    example one file per country): a later run that covers a different country list does not collide with an earlier run
    over the files they share, but the same file written under different settings does. All claims are validated before
    any is recorded, so a refusal part-way through leaves no new record behind. ``--overwrite`` on the namespace is honoured.
    """
    base = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items() if k not in exclude}
    ow = bool(getattr(args, "overwrite", False))
    prepared = []
    for path, overrides in items:
        overrides = dict(overrides or {})
        params = {k: v for k, v in base.items() if k not in overrides}
        params.update({k: (str(v) if isinstance(v, Path) else v) for k, v in overrides.items()})
        prepared.append((Path(path), params))
    if not ow:
        for p, params in prepared:                       # validate everything first
            side = sidecar_path(p)
            if side.exists():
                if json.loads(side.read_text(encoding="utf-8")).get("fingerprint") != fingerprint(params):
                    raise OutputCollision(f"{p} was written by a different run. Use a distinct --out or pass --overwrite.")
            elif p.exists():
                raise OutputCollision(f"{p} already exists and has no run record, so its origin is unknown. "
                                      "Use a distinct --out or pass --overwrite to discard it.")
    return [claim_output(p, params, overwrite=ow) for p, params in prepared]
