"""Storage backend selector for mempalace.

Controls which vector store backs the palace at import time. Default
behaviour is unchanged — we import ``chromadb``. Setting
``MEMPAL_STORAGE=palace_store`` swaps in the ``palace_store.compat``
drop-in shim for the full duration of the process.

All modules that used to write ``import chromadb`` should instead do::

    from ._storage_backend import chromadb

That leaves a single switch point for the POC and makes rollback a
one-line change in one file.
"""

from __future__ import annotations

import os


_backend = os.environ.get("MEMPAL_STORAGE", "chromadb").strip().lower()

# Pre-import chromadb eagerly even under palace_store, so its fragile
# top-level init runs once in a clean context. Without this, the first
# nested ``import chromadb`` from an unrelated code path (e.g. the
# Chroma-specific ``cmd_repair`` that can't go through the selector)
# triggers an ONNXMiniLM_L6_V2 NameError from a half-initialized module.
# This adds a small import-time cost but avoids a cross-test state
# corruption that's a chromadb bug, not ours.
try:
    import chromadb as _real_chromadb  # noqa: F401
except ImportError:
    _real_chromadb = None

if _backend in ("palace", "palace_store", "palacestore"):
    # Drop-in shim built on PalaceStore
    from palace_store import compat as chromadb  # noqa: F401
    BACKEND_NAME = "palace_store"
elif _backend in ("", "chromadb", "chroma"):
    if _real_chromadb is None:
        raise RuntimeError(
            "chromadb is not installed; set MEMPAL_STORAGE=palace_store "
            "to use the bespoke backend instead."
        )
    chromadb = _real_chromadb  # noqa: F401
    BACKEND_NAME = "chromadb"
else:
    raise RuntimeError(
        f"MEMPAL_STORAGE={_backend!r} is not a valid backend. "
        f"Use 'chromadb' (default) or 'palace_store'."
    )


__all__ = ["chromadb", "BACKEND_NAME"]
