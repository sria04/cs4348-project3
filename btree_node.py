"""B-tree node layout: one 512-byte block per node (minimal degree 10 → max 19 keys)."""

from __future__ import annotations

from dataclasses import dataclass

import index_file

MIN_DEGREE = 10
MAX_KEYS = 2 * MIN_DEGREE - 1  # 19
NUM_CHILDREN = MAX_KEYS + 1  # 20

# Payload starts after block_id, parent_id, num_keys (8+8+8 bytes).
_NODE_META_END = 24


@dataclass
class Node:
    block_id: int
    parent_id: int
    num_keys: int
    keys: list[int]
    values: list[int]
    children: list[int]

    def __post_init__(self) -> None:
        if len(self.keys) != MAX_KEYS:
            raise ValueError(f"keys must have length {MAX_KEYS}")
        if len(self.values) != MAX_KEYS:
            raise ValueError(f"values must have length {MAX_KEYS}")
        if len(self.children) != NUM_CHILDREN:
            raise ValueError(f"children must have length {NUM_CHILDREN}")


def empty_node(block_id: int, parent_id: int = 0) -> Node:
    z = [0] * MAX_KEYS
    c = [0] * NUM_CHILDREN
    return Node(block_id, parent_id, 0, list(z), list(z), list(c))


def encode_node_block(node: Node) -> bytes:
    if node.num_keys < 0 or node.num_keys > MAX_KEYS:
        raise ValueError("num_keys out of range")

    buf = bytearray(index_file.BLOCK_SIZE)
    buf[0:8] = index_file.pack_u64(node.block_id)
    buf[8:16] = index_file.pack_u64(node.parent_id)
    buf[16:24] = index_file.pack_u64(node.num_keys)

    off = _NODE_META_END
    for i in range(MAX_KEYS):
        buf[off : off + 8] = index_file.pack_u64(node.keys[i])
        off += 8
    for i in range(MAX_KEYS):
        buf[off : off + 8] = index_file.pack_u64(node.values[i])
        off += 8
    for i in range(NUM_CHILDREN):
        buf[off : off + 8] = index_file.pack_u64(node.children[i])
        off += 8
    # bytes 488–511 left as zero
    return bytes(buf)


def decode_node_block(data: bytes) -> Node:
    if len(data) != index_file.BLOCK_SIZE:
        raise ValueError("node block must be 512 bytes")
    block_id = index_file.unpack_u64(data[0:8])
    parent_id = index_file.unpack_u64(data[8:16])
    num_keys = index_file.unpack_u64(data[16:24])
    if num_keys > MAX_KEYS:
        raise ValueError("invalid num_keys in block")

    keys: list[int] = []
    values: list[int] = []
    children: list[int] = []
    off = _NODE_META_END
    for _ in range(MAX_KEYS):
        keys.append(index_file.unpack_u64(data[off : off + 8]))
        off += 8
    for _ in range(MAX_KEYS):
        values.append(index_file.unpack_u64(data[off : off + 8]))
        off += 8
    for _ in range(NUM_CHILDREN):
        children.append(index_file.unpack_u64(data[off : off + 8]))
        off += 8

    return Node(block_id, parent_id, num_keys, keys, values, children)
