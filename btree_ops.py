"""B-tree operations on an open index file (one node decoded in memory at a time during search)."""

from __future__ import annotations

from typing import BinaryIO

import btree_node
import index_file


def _is_leaf(node: btree_node.Node) -> bool:
    return all(c == 0 for c in node.children)


def search_key(f: BinaryIO, key: int) -> tuple[int, int] | None:
    """
    Return (key, value) if found, else None.
    Loads at most one node block at a time from disk (previous node is discarded each step).
    """
    root_id, _ = index_file.read_header_from_open_file(f)
    if root_id == 0:
        return None

    block_id = root_id
    while True:
        raw = index_file.read_block(f, block_id)
        node = btree_node.decode_node_block(raw)

        i = 0
        n = node.num_keys
        while i < n and key > node.keys[i]:
            i += 1
        if i < n and key == node.keys[i]:
            return (key, node.values[i])
        if _is_leaf(node):
            return None

        child_id = node.children[i]
        if child_id == 0:
            return None
        block_id = child_id
