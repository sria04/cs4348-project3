"""B-tree operations on an open index file (one node decoded in memory at a time during search)."""

from __future__ import annotations

from typing import BinaryIO

import btree_node
import index_file


class DuplicateKeyError(Exception):
    """Key already present in the tree."""


class LeafFullError(Exception):
    """Leaf insert attempted while full (should not happen if splits run correctly)."""


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


def _set_parent(f: BinaryIO, block_id: int, parent_id: int) -> None:
    raw = index_file.read_block(f, block_id)
    node = btree_node.decode_node_block(raw)
    node.parent_id = parent_id
    index_file.write_block(f, block_id, btree_node.encode_node_block(node))


def _check_duplicate_in_node(node: btree_node.Node, key: int) -> None:
    for i in range(node.num_keys):
        if node.keys[i] == key:
            raise DuplicateKeyError


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


def _split_child(f: BinaryIO, parent_id: int, i: int) -> None:
    """
    Split parent's full i-th child (2t-1 keys) into two nodes with t-1 keys each;
    move the middle key into parent at index i. Parent must have room (< 2t-1 keys).
    """
    t = btree_node.MIN_DEGREE
    mid = t - 1  # index of key promoted from full child (19 keys → promote keys[9])

    parent_raw = index_file.read_block(f, parent_id)
    parent = btree_node.decode_node_block(parent_raw)
    if parent.num_keys >= btree_node.MAX_KEYS:
        raise ValueError("parent full: cannot split child")

    y_id = parent.children[i]
    y_raw = index_file.read_block(f, y_id)
    y = btree_node.decode_node_block(y_raw)
    if y.num_keys != btree_node.MAX_KEYS:
        raise ValueError("child not full")

    promote_k = y.keys[mid]
    promote_v = y.values[mid]

    z_id = _allocate_block(f)
    z = btree_node.empty_node(z_id, parent_id)

    if _is_leaf(y):
        z.num_keys = t - 1
        for j in range(t - 1):
            z.keys[j] = y.keys[j + t]
            z.values[j] = y.values[j + t]
        y.num_keys = t - 1
        for j in range(t - 1, btree_node.MAX_KEYS):
            y.keys[j] = 0
            y.values[j] = 0
    else:
        z.num_keys = t - 1
        for j in range(t - 1):
            z.keys[j] = y.keys[j + t]
            z.values[j] = y.values[j + t]
        for j in range(t):
            z.children[j] = y.children[j + t]
            if z.children[j] != 0:
                _set_parent(f, z.children[j], z_id)
        y.num_keys = t - 1
        for j in range(mid, btree_node.MAX_KEYS):
            y.keys[j] = 0
            y.values[j] = 0
        for j in range(t, btree_node.NUM_CHILDREN):
            y.children[j] = 0

    n = parent.num_keys
    for j in range(n, i, -1):
        parent.keys[j] = parent.keys[j - 1]
        parent.values[j] = parent.values[j - 1]
    for j in range(n + 1, i + 1, -1):
        parent.children[j] = parent.children[j - 1]
    parent.keys[i] = promote_k
    parent.values[i] = promote_v
    parent.children[i + 1] = z_id
    parent.num_keys = n + 1

    index_file.write_block(f, y_id, btree_node.encode_node_block(y))
    index_file.write_block(f, z_id, btree_node.encode_node_block(z))
    index_file.write_block(f, parent_id, btree_node.encode_node_block(parent))


def _insert_non_full(f: BinaryIO, x_id: int, key: int, value: int) -> None:
    x_raw = index_file.read_block(f, x_id)
    x = btree_node.decode_node_block(x_raw)
    _check_duplicate_in_node(x, key)

    if _is_leaf(x):
        _insert_sorted_into_leaf(x, key, value)
        index_file.write_block(f, x_id, btree_node.encode_node_block(x))
        return

    i = 0
    while i < x.num_keys and key > x.keys[i]:
        i += 1
    if i < x.num_keys and key == x.keys[i]:
        raise DuplicateKeyError

    child_id = x.children[i]
    child_raw = index_file.read_block(f, child_id)
    child = btree_node.decode_node_block(child_raw)

    if child.num_keys == btree_node.MAX_KEYS:
        _split_child(f, x_id, i)
        x = btree_node.decode_node_block(index_file.read_block(f, x_id))
        if key > x.keys[i]:
            i += 1
        child_id = x.children[i]

    _insert_non_full(f, child_id, key, value)


def insert_key(f: BinaryIO, key: int, value: int) -> None:
    """Insert key/value, splitting nodes as needed (including a full root)."""
    root_id, _ = index_file.read_header_from_open_file(f)
    if root_id == 0:
        new_id = _allocate_block(f)
        _, next_after = index_file.read_header_from_open_file(f)
        leaf = btree_node.empty_node(new_id, parent_id=0)
        _insert_sorted_into_leaf(leaf, key, value)
        index_file.write_block(f, new_id, btree_node.encode_node_block(leaf))
        index_file.write_header(f, new_id, next_after)
        return

    r_raw = index_file.read_block(f, root_id)
    r = btree_node.decode_node_block(r_raw)
    if r.num_keys == btree_node.MAX_KEYS:
        s_id = _allocate_block(f)
        _, next_after = index_file.read_header_from_open_file(f)
        s = btree_node.empty_node(s_id, parent_id=0)
        s.children[0] = root_id
        index_file.write_block(f, s_id, btree_node.encode_node_block(s))
        _set_parent(f, root_id, s_id)
        index_file.write_header(f, s_id, next_after)
        _split_child(f, s_id, 0)
        root_id, _ = index_file.read_header_from_open_file(f)

    _insert_non_full(f, root_id, key, value)


def _inorder_collect(f: BinaryIO, block_id: int, out: list[tuple[int, int]]) -> None:
    """Append all key/value pairs under this subtree in sorted key order."""
    if block_id == 0:
        return
    raw = index_file.read_block(f, block_id)
    node = btree_node.decode_node_block(raw)
    if _is_leaf(node):
        for i in range(node.num_keys):
            out.append((node.keys[i], node.values[i]))
        return
    for i in range(node.num_keys):
        _inorder_collect(f, node.children[i], out)
        out.append((node.keys[i], node.values[i]))
    _inorder_collect(f, node.children[node.num_keys], out)


def all_pairs_inorder(f: BinaryIO) -> list[tuple[int, int]]:
    root_id, _ = index_file.read_header_from_open_file(f)
    if root_id == 0:
        return []
    out: list[tuple[int, int]] = []
    _inorder_collect(f, root_id, out)
    return out
