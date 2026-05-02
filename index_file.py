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
        with open(path, "rb") as f:
            if os.path.getsize(path) % BLOCK_SIZE != 0:
                return False
            read_header_from_open_file(f)
    except (OSError, ValueError):
        return False
    return True
