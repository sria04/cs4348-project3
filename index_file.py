"""512-byte block layout, header, and raw block I/O for B-tree index files."""

from __future__ import annotations

import os
from typing import BinaryIO

BLOCK_SIZE = 512
UINT64_SIZE = 8
MAGIC = b"4348PRJ3"
HEADER_MAGIC_END = 8
HEADER_ROOT_END = 16
HEADER_NEXT_END = 24


def pack_u64(n: int) -> bytes:
    return int(n).to_bytes(UINT64_SIZE, "big", signed=False)


def unpack_u64(data: bytes) -> int:
    return int.from_bytes(data[:UINT64_SIZE], "big", signed=False)


UINT64_MAX = 2**64 - 1


def parse_uint64_key(s: str) -> int:
    """Parse a non-negative decimal integer that fits in 64 bits (insert/search/load)."""
    t = s.strip()
    if not t or t[0] == "-":
        raise ValueError("integer must be non-negative")
    n = int(t, 10)
    if n < 0 or n > UINT64_MAX:
        raise ValueError("integer out of uint64 range")
    return n


def build_header_block(root_block_id: int, next_block_id: int) -> bytes:
    buf = bytearray(BLOCK_SIZE)
    buf[0:HEADER_MAGIC_END] = MAGIC
    buf[HEADER_MAGIC_END:HEADER_ROOT_END] = pack_u64(root_block_id)
    buf[HEADER_ROOT_END:HEADER_NEXT_END] = pack_u64(next_block_id)
    return bytes(buf)


def parse_header_block(data: bytes) -> tuple[int, int]:
    if len(data) < HEADER_NEXT_END:
        raise ValueError("header too short")
    if data[0:HEADER_MAGIC_END] != MAGIC:
        raise ValueError("invalid magic")
    root = unpack_u64(data[HEADER_MAGIC_END:HEADER_ROOT_END])
    next_id = unpack_u64(data[HEADER_ROOT_END:HEADER_NEXT_END])
    return root, next_id


def read_block(f: BinaryIO, block_id: int) -> bytes:
    f.seek(block_id * BLOCK_SIZE)
    data = f.read(BLOCK_SIZE)
    if len(data) != BLOCK_SIZE:
        raise ValueError("short read or past end of file")
    return data


def write_block(f: BinaryIO, block_id: int, data: bytes) -> None:
    if len(data) > BLOCK_SIZE:
        raise ValueError("block data exceeds 512 bytes")
    padded = data.ljust(BLOCK_SIZE, b"\x00")
    f.seek(block_id * BLOCK_SIZE)
    f.write(padded)


def read_header_from_open_file(f: BinaryIO) -> tuple[int, int]:
    return parse_header_block(read_block(f, 0))


def write_header(f: BinaryIO, root_block_id: int, next_block_id: int) -> None:
    write_block(f, 0, build_header_block(root_block_id, next_block_id))


def create_index(path: str) -> None:
    if os.path.exists(path):
        raise FileExistsError(path)
    header = build_header_block(root_block_id=0, next_block_id=1)
    with open(path, "wb") as out:
        out.write(header)


def is_valid_index_file(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        size = os.path.getsize(path)
        if size == 0 or size % BLOCK_SIZE != 0:
            return False
        num_blocks = size // BLOCK_SIZE
        with open(path, "rb") as f:
            root_id, next_id = read_header_from_open_file(f)
        if next_id != num_blocks:
            return False
        if root_id != 0 and root_id >= next_id:
            return False
    except (OSError, ValueError):
        return False
    return True
