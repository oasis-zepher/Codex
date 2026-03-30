from __future__ import annotations

import os
from pathlib import Path


def expand_visible_path(path_value: str | Path, *, base_dir: Path | None = None) -> Path:
    """Expand a path without resolving symlinked temp prefixes like ``/var`` -> ``/private/var``."""

    path = Path(path_value).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return Path(os.path.abspath(os.fspath(path)))
