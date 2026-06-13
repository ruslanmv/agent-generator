"""Strict deterministic packager (Batch 6).

Writes a Matrix Bundle ZIP that is byte-identical across machines and runs:

* fixed file ordering (sorted paths),
* fixed timestamps (the ZIP epoch, 1980-01-01),
* fixed permissions and a fixed compression level,
* LF-normalized content (normalization happens at compile time so digests match the bytes).

Determinism here is a correctness property: it is what lets two versions of a bundle be
diffed and lets golden snapshots detect unintended change.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping
from pathlib import Path

# 1980-01-01 00:00:00 — the earliest timestamp the ZIP format can represent.
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
_FILE_MODE = 0o644 << 16


def _write(zf: zipfile.ZipFile, file_map: Mapping[str, str]) -> None:
    for path in sorted(file_map):
        info = zipfile.ZipInfo(filename=path, date_time=_ZIP_EPOCH)
        info.external_attr = _FILE_MODE
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, file_map[path].encode("utf-8"))


def write_strict_zip(file_map: Mapping[str, str], out_path: str | Path) -> Path:
    """Write ``file_map`` to a deterministic ZIP at ``out_path``."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        _write(zf, file_map)
    return out


def zip_bytes(file_map: Mapping[str, str]) -> bytes:
    """Return a deterministic ZIP of ``file_map`` as bytes (for HTTP streaming)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        _write(zf, file_map)
    return buffer.getvalue()


__all__ = ["write_strict_zip", "zip_bytes"]
