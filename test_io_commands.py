"""Tests for print, extract, and load commands."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

import btree_ops
import index_file


class TestAllPairsInorder(unittest.TestCase):
    def test_matches_manual_tree(self) -> None:
        # Same layout as test_btree_search internal+two-leaves (keys 10, 50, 60).
        import btree_node

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
            with open(path, "wb") as f:
                f.write(index_file.build_header_block(1, 4))
                index_file.write_block(f, 1, btree_node.encode_node_block(root))
                index_file.write_block(f, 2, btree_node.encode_node_block(left))
                index_file.write_block(f, 3, btree_node.encode_node_block(right))
            with open(path, "rb") as f:
                pairs = btree_ops.all_pairs_inorder(f)
        self.assertEqual(pairs, [(10, 10), (50, 500), (60, 60)])


class TestPrintExtractLoadCLI(unittest.TestCase):
    def setUp(self) -> None:
        self._root = os.path.dirname(os.path.abspath(__file__))

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "project3.py", *args],
            cwd=self._root,
            capture_output=True,
            text=True,
        )

    def test_print_sorted_and_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            idx = os.path.join(d, "a.idx")
            self._run("create", idx).check_returncode()
            r0 = self._run("print", idx)
            self.assertEqual(r0.returncode, 0)
            self.assertEqual(r0.stdout, "")
            self._run("insert", idx, "30", "3").check_returncode()
            self._run("insert", idx, "10", "1").check_returncode()
            self._run("insert", idx, "20", "2").check_returncode()
            r = self._run("print", idx)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "10 1\n20 2\n30 3\n")

    def test_extract_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            idx = os.path.join(d, "b.idx")
            out = os.path.join(d, "out.csv")
            inp = os.path.join(d, "in.csv")
            self._run("create", idx).check_returncode()
            self._run("insert", idx, "5", "50").check_returncode()
            self._run("insert", idx, "1", "10").check_returncode()
            self._run("extract", idx, out).check_returncode()
            with open(out, encoding="utf-8") as f:
                body = f.read()
            self.assertEqual(body, "1,10\n5,50\n")
            idx2 = os.path.join(d, "c.idx")
            self._run("create", idx2).check_returncode()
            with open(inp, "w", encoding="utf-8") as f:
                f.write(body)
            self._run("load", idx2, inp).check_returncode()
            r = self._run("print", idx2)
            self.assertEqual(r.stdout, "1 10\n5 50\n")

    def test_extract_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            idx = os.path.join(d, "d.idx")
            out = os.path.join(d, "exists.csv")
            self._run("create", idx).check_returncode()
            with open(out, "w") as f:
                f.write("x\n")
            r = self._run("extract", idx, out)
            self.assertNotEqual(r.returncode, 0)
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "x\n")

    def test_load_missing_csv(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            idx = os.path.join(d, "e.idx")
            self._run("create", idx).check_returncode()
            r = self._run("load", idx, os.path.join(d, "nope.csv"))
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
