"""B-tree operations on an open index file (one node decoded in memory at a time during search)."""

from __future__ import annotations

from typing import BinaryIO

import btree_node
import index_file


class DuplicateKeyError(Exception):
    """Key already present in the tree."""


class LeafFullError(Exception):
    """Target leaf has 19 keys; split not yet applied."""


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


def _allocate_block(f: BinaryIO) -> int:
    """Use next_block_id as a new node block; increment next in the header (root unchanged)."""
    root, next_b = index_file.read_header_from_open_file(f)
    new_id = next_b
    index_file.write_header(f, root, next_b + 1)
    return new_id


def _check_duplicate_in_node(node: btree_node.Node, key: int) -> None:
    for i in range(node.num_keys):
        if node.keys[i] == key:
            raise DuplicateKeyError


def _find_leaf_for_insert(f: BinaryIO, key: int) -> tuple[int, btree_node.Node]:
    root_id, _ = index_file.read_header_from_open_file(f)
    if root_id == 0:
        raise ValueError("empty tree")
    block_id = root_id
    while True:
        raw = index_file.read_block(f, block_id)
        node = btree_node.decode_node_block(raw)
        _check_duplicate_in_node(node, key)
        if _is_leaf(node):
            return block_id, node
        i = 0
        n = node.num_keys
        while i < n and key > node.keys[i]:
            i += 1
        child_id = node.children[i]
        if child_id == 0:
            raise ValueError("corrupt tree: missing child")
        block_id = child_id


def _insert_sorted_into_leaf(node: btree_node.Node, key: int, value: int) -> None:
    n = node.num_keys
    if n >= btree_node.MAX_KEYS:
        raise LeafFullError
    i = 0
    while i < n and key > node.keys[i]:
        i += 1
    if i < n and key == node.keys[i]:
        raise DuplicateKeyError
    for j in range(n, i, -1):
        node.keys[j] = node.keys[j - 1]
        node.values[j] = node.values[j - 1]
    node.keys[i] = key
    node.values[i] = value
    node.num_keys = n + 1


def insert_key(f: BinaryIO, key: int, value: int) -> None:
    """
    Insert key/value into a leaf with spare capacity, or create the first leaf if the tree is empty.
    Does not split full nodes (raises LeafFullError).
    """
    root_id, _ = index_file.read_header_from_open_file(f)
    if root_id == 0:
        new_id = _allocate_block(f)
        _, next_after = index_file.read_header_from_open_file(f)
        leaf = btree_node.empty_node(new_id, parent_id=0)
        _insert_sorted_into_leaf(leaf, key, value)
        index_file.write_block(f, new_id, btree_node.encode_node_block(leaf))
        index_file.write_header(f, new_id, next_after)
        return

    leaf_id, leaf = _find_leaf_for_insert(f, key)
    if leaf.num_keys >= btree_node.MAX_KEYS:
        raise LeafFullError
    _insert_sorted_into_leaf(leaf, key, value)
    index_file.write_block(f, leaf_id, btree_node.encode_node_block(leaf))
