from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from codex_research_assist.path_utils import expand_visible_path


class PathUtilsTest(unittest.TestCase):
    def test_expand_visible_path_preserves_temp_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "artifact.json"

            resolved = expand_visible_path(target)

        self.assertEqual(resolved.as_posix(), target.as_posix())

    def test_expand_visible_path_joins_relative_paths_without_symlink_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            resolved = expand_visible_path("nested/file.txt", base_dir=root)

        self.assertEqual(resolved.as_posix(), (root / "nested" / "file.txt").as_posix())


if __name__ == "__main__":
    unittest.main()
