"""Round-trip tests for B-tree node block encoding (stdlib unittest)."""

from __future__ import annotations

import unittest

import btree_node


class TestNodeRoundtrip(unittest.TestCase):
    def test_empty_leaf_roundtrip(self) -> None:
        n = btree_node.empty_node(block_id=3, parent_id=1)
        raw = btree_node.encode_node_block(n)
        self.assertEqual(len(raw), 512)
        back = btree_node.decode_node_block(raw)
        self.assertEqual(back.block_id, 3)
        self.assertEqual(back.parent_id, 1)
        self.assertEqual(back.num_keys, 0)
        self.assertEqual(back.keys, [0] * btree_node.MAX_KEYS)
        self.assertEqual(back.values, [0] * btree_node.MAX_KEYS)
        self.assertEqual(back.children, [0] * btree_node.NUM_CHILDREN)

    def test_partial_keys_roundtrip(self) -> None:
        n = btree_node.empty_node(block_id=7, parent_id=2)
        n.num_keys = 3
        n.keys[0], n.keys[1], n.keys[2] = 10, 20, 30
        n.values[0], n.values[1], n.values[2] = 100, 200, 300
        n.children[0] = 4
        n.children[1] = 5
        n.children[2] = 6
        n.children[3] = 8
        raw = btree_node.encode_node_block(n)
        back = btree_node.decode_node_block(raw)
        self.assertEqual(back.num_keys, 3)
        self.assertEqual(back.keys[:3], [10, 20, 30])
        self.assertEqual(back.values[:3], [100, 200, 300])
        self.assertEqual(back.children[:4], [4, 5, 6, 8])

    def test_full_node_roundtrip(self) -> None:
        n = btree_node.empty_node(block_id=1, parent_id=0)
        n.num_keys = btree_node.MAX_KEYS
        for i in range(btree_node.MAX_KEYS):
            n.keys[i] = i + 1
            n.values[i] = (i + 1) * 1000
        for i in range(btree_node.NUM_CHILDREN):
            n.children[i] = i + 100
        raw = btree_node.encode_node_block(n)
        back = btree_node.decode_node_block(raw)
        self.assertEqual(back.keys, n.keys)
        self.assertEqual(back.values, n.values)
        self.assertEqual(back.children, n.children)

    def test_encode_rejects_bad_num_keys(self) -> None:
        n = btree_node.empty_node(1, 0)
        n.num_keys = 20
        with self.assertRaises(ValueError):
            btree_node.encode_node_block(n)


if __name__ == "__main__":
    unittest.main()
