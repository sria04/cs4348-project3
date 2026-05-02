"""Tests for index file validation and corrupt-file CLI errors."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

import index_file


class TestIsValidIndexFile(unittest.TestCase):
    def test_good_empty_and_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.idx")
            index_file.create_index(path)
            self.assertTrue(index_file.is_valid_index_file(path))

    def test_rejects_bad_magic(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "b.idx")
            with open(path, "wb") as f:
                f.write(b"BADMAGIC" + b"\x00" * (index_file.BLOCK_SIZE - 8))
            self.assertFalse(index_file.is_valid_index_file(path))

    def test_rejects_non_multiple_of_block(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.idx")
            with open(path, "wb") as f:
                f.write(b"\x00" * 100)
            self.assertFalse(index_file.is_valid_index_file(path))

    def test_rejects_next_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "d.idx")
            with open(path, "wb") as f:
                f.write(index_file.build_header_block(0, 5))
            self.assertFalse(index_file.is_valid_index_file(path))

    def test_rejects_root_out_of_range(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "e.idx")
            with open(path, "wb") as f:
                f.write(index_file.build_header_block(99, 1))
            self.assertFalse(index_file.is_valid_index_file(path))


class TestCorruptIndexCLI(unittest.TestCase):
    def setUp(self) -> None:
        self._root = os.path.dirname(os.path.abspath(__file__))

    def test_search_rejects_invalid_magic_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.idx")
            with open(path, "wb") as f:
                f.write(b"NOTPRJ3!" + b"\x00" * (index_file.BLOCK_SIZE - 8))
            r = subprocess.run(
                [sys.executable, "project3.py", "search", path, "1"],
                cwd=self._root,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("invalid", r.stderr.lower())


if __name__ == "__main__":
    unittest.main()
