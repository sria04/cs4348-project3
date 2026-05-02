"""Tests for on-disk B-tree search and the search CLI."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

import btree_node
import btree_ops
import index_file


def _write_index(path: str, root_id: int, next_id: int, nodes: dict[int, bytes]) -> None:
    with open(path, "wb") as f:
        f.write(index_file.build_header_block(root_id, next_id))
        for block_id in sorted(nodes):
            index_file.write_block(f, block_id, nodes[block_id])


class TestSearchOnDisk(unittest.TestCase):
    def test_empty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "e.idx")
            index_file.create_index(path)
            with open(path, "rb") as f:
                self.assertIsNone(btree_ops.search_key(f, 42))

    def test_single_leaf_root(self) -> None:
        leaf = btree_node.empty_node(block_id=1, parent_id=0)
        leaf.num_keys = 2
        leaf.keys[0], leaf.keys[1] = 10, 30
        leaf.values[0], leaf.values[1] = 100, 300

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.idx")
            _write_index(
                path,
                root_id=1,
                next_id=2,
                nodes={1: btree_node.encode_node_block(leaf)},
            )
            with open(path, "rb") as f:
                self.assertEqual(btree_ops.search_key(f, 10), (10, 100))
                self.assertEqual(btree_ops.search_key(f, 30), (30, 300))
                self.assertIsNone(btree_ops.search_key(f, 20))

    def test_internal_and_leaves(self) -> None:
        root = btree_node.empty_node(block_id=1, parent_id=0)
        root.num_keys = 1
        root.keys[0] = 50
        root.values[0] = 500
        root.children[0] = 2
        root.children[1] = 3

        left = btree_node.empty_node(block_id=2, parent_id=1)
        left.num_keys = 1
        left.keys[0] = 10
        left.values[0] = 10

        right = btree_node.empty_node(block_id=3, parent_id=1)
        right.num_keys = 1
        right.keys[0] = 60
        right.values[0] = 60

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.idx")
            _write_index(
                path,
                root_id=1,
                next_id=4,
                nodes={
                    1: btree_node.encode_node_block(root),
                    2: btree_node.encode_node_block(left),
                    3: btree_node.encode_node_block(right),
                },
            )
            with open(path, "rb") as f:
                self.assertEqual(btree_ops.search_key(f, 50), (50, 500))
                self.assertEqual(btree_ops.search_key(f, 10), (10, 10))
                self.assertEqual(btree_ops.search_key(f, 60), (60, 60))
                self.assertIsNone(btree_ops.search_key(f, 40))


class TestSearchCLI(unittest.TestCase):
    def setUp(self) -> None:
        self._root = os.path.dirname(os.path.abspath(__file__))

    def test_cli_empty_index(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.idx")
            subprocess.run(
                [sys.executable, "project3.py", "create", path],
                cwd=self._root,
                check=True,
            )
            r = subprocess.run(
                [sys.executable, "project3.py", "search", path, "1"],
                cwd=self._root,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("not found", r.stderr.lower())


if __name__ == "__main__":
    unittest.main()
