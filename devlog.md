# Development log — CS4348 Project 3

## Session 1 — Scaffold (commit 1)

**Goal:** Repository layout, `.gitignore`, README skeleton, and a CLI entrypoint that parses all required subcommands with correct arguments (per assignment), without implementing B-tree or file I/O yet.

**What changed:**

- Added `project3.py` with `argparse` subparsers: `create`, `insert`, `search`, `load`, `print`, `extract`. Each command still exits with a stub message; `--help` documents usage.
- Added `.gitignore` for Python caches, virtualenvs, and local `*.idx` / `*.csv` test artifacts.
- Added `README.md` with run instructions (`python3 project3.py …`) and a command summary table.

**How tested:**

- `python3 project3.py --help` and `python3 project3.py <subcommand> --help` show expected usage.
- Running a subcommand prints a clear “not implemented” message to stderr and non-zero exit (stub).

**Next:** Block I/O and file header (`create` producing a valid empty index file); constants for block size, magic string, endianness.

## Session 2 — Block layer and `create`

**Goal:** 512-byte blocks, big-endian `uint64` fields, header layout from the spec, raw `read_block` / `write_block`, and a working `create` that refuses to clobber an existing file.

**What changed:**

- New `index_file.py`: `BLOCK_SIZE`, `MAGIC` (`4348PRJ3`), `pack_u64` / `unpack_u64`, `build_header_block` / `parse_header_block`, `read_block` / `write_block`, `read_header_from_open_file`, `create_index`, and `is_valid_index_file` (for later commands).
- Empty index: root block id `0`, next block id `1` (block `0` is header only).
- `project3.py`: `create` calls `create_index`; duplicate path → error message on stderr, exit `1`.

**How tested:**

- `python3 project3.py create new.idx` then file size is `512` bytes; first 8 bytes are ASCII `4348PRJ3`; parsed header gives root `0`, next `1`.
- Second `create` on same path fails without changing the file.

**Next:** Node block encode/decode (19 keys, 19 values, 20 child ids); round-trip tests; then `search` / insert path.

## Session 3 — Node block encoding

**Goal:** Serialize and deserialize one B-tree node into exactly 512 bytes per the assignment field order; verify with automated tests.

**What changed:**

- New `btree_node.py`: `MIN_DEGREE` / `MAX_KEYS` / `NUM_CHILDREN`, `Node` dataclass, `empty_node`, `encode_node_block`, `decode_node_block` (big-endian u64 via `index_file`).
- New `test_btree_node.py`: unittest cases for empty node, partial keys, full 19-key node, and invalid `num_keys` on encode.

**How tested:**

- `python3 -m unittest -v` (all tests pass).

**Next:** Open index + load nodes from disk with the 3-node memory limit in mind; implement `search` on an empty then single-node tree.

## Session 4 — `search`

**Goal:** B-tree lookup from the root block id in the header; validate index path; print `key value` on success; sensible errors for bad file, bad key text, or missing key.

**What changed:**

- `index_file.parse_uint64_key` for decimal uint64 CLI arguments.
- `btree_ops.search_key`: standard B-tree descent; leaf = all child ids zero; only one node is decoded at a time (previous block discarded each step), under the assignment’s 3-node cap.
- `project3.py`: `search` subcommand wired to the above.
- `test_btree_search.py`: empty index, single-leaf root, internal+two-leaves fixture, plus a subprocess smoke test on an empty tree.

**How tested:**

- `python3 -m unittest -v`

**Next:** `insert` into leaf (no split), then splits and root growth; keep the same on-disk discipline.
