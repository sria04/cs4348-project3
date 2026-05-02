"""Tests for insert without node split."""

from __future__ import annotations

import os
import random
import subprocess
import sys
import tempfile
import unittest

import btree_node
import btree_ops
import index_file


class TestInsertNoSplit(unittest.TestCase):
    def test_first_key_then_search(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.idx")
            index_file.create_index(path)
            with open(path, "r+b") as f:
                btree_ops.insert_key(f, 15, 100)
            with open(path, "rb") as f:
                self.assertEqual(btree_ops.search_key(f, 15), (15, 100))

    def test_multiple_keys_one_leaf(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "b.idx")
            index_file.create_index(path)
            with open(path, "r+b") as f:
                for k, v in [(5, 50), (20, 200), (10, 100)]:
                    btree_ops.insert_key(f, k, v)
            with open(path, "rb") as f:
                self.assertEqual(btree_ops.search_key(f, 5), (5, 50))
                self.assertEqual(btree_ops.search_key(f, 10), (10, 100))
                self.assertEqual(btree_ops.search_key(f, 20), (20, 200))

    def test_duplicate_raises(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.idx")
            index_file.create_index(path)
            with open(path, "r+b") as f:
                btree_ops.insert_key(f, 1, 2)
                with self.assertRaises(btree_ops.DuplicateKeyError):
                    btree_ops.insert_key(f, 1, 99)

    def test_many_inserts_split(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "d.idx")
            index_file.create_index(path)
            n = 250
            with open(path, "r+b") as f:
                for i in range(n):
                    btree_ops.insert_key(f, i, i * 10 + 7)
            with open(path, "rb") as f:
                for i in range(n):
                    self.assertEqual(
                        btree_ops.search_key(f, i),
                        (i, i * 10 + 7),
                    )

    def test_many_inserts_random_order(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "e.idx")
            index_file.create_index(path)
            keys = list(range(80))
            rnd = random.Random(42)
            rnd.shuffle(keys)
            with open(path, "r+b") as f:
                for k in keys:
                    btree_ops.insert_key(f, k, k * 3)
            with open(path, "rb") as f:
                for k in keys:
                    self.assertEqual(btree_ops.search_key(f, k), (k, k * 3))


class TestInsertCLI(unittest.TestCase):
    def setUp(self) -> None:
        self._root = os.path.dirname(os.path.abspath(__file__))

    def test_cli_insert_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.idx")
            subprocess.run(
                [sys.executable, "project3.py", "create", path],
                cwd=self._root,
                check=True,
            )
            subprocess.run(
                [sys.executable, "project3.py", "insert", path, "15", "100"],
                cwd=self._root,
                check=True,
            )
            r = subprocess.run(
                [sys.executable, "project3.py", "search", path, "15"],
                cwd=self._root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "15 100")


if __name__ == "__main__":
    unittest.main()
