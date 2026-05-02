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

## Session 5 — `insert` (no split)

**Goal:** Insert into an empty tree (first leaf + header update) or into a non-full leaf; reject duplicates and full leaves (19 keys) until splits exist.

**What changed:**

- `index_file.write_header` for atomic header updates on an open file.
- `btree_ops`: `_allocate_block`, `_find_leaf_for_insert`, `_insert_sorted_into_leaf`, `insert_key`; `DuplicateKeyError` and `LeafFullError`. (Session 6 replaces the insert path with `_insert_non_full` / `_split_child` and drops `_find_leaf_for_insert`.)
- `project3.py`: `insert` parses key/value as uint64, opens `r+b`, surfaces errors on stderr.
- `test_btree_insert.py`: first key, multi-key leaf, duplicate, leaf full, CLI insert+search.

**How tested:**

- `python3 -m unittest -v`

**Next:** Split full leaves and internal nodes; grow height when the root splits.

## Session 6 — Splits and full `insert`

**Goal:** CLRS-style B-tree insert: split full children on the way down, split a full root by introducing a new empty parent, redistribute keys/children with middle key promoted; keep `parent_id` updated for moved internal children.

**What changed:**

- `btree_ops._split_child`, `_insert_non_full`, `_set_parent`; `insert_key` handles empty tree, full-root split, then recursive insert.
- Split parameters: `t = 10`, promote key at index `t - 1`, left/right leaves (or internals) each hold `t - 1` keys.
- `test_btree_insert`: replaced “leaf full” expectation with `test_many_inserts_split` (250 keys) and `test_many_inserts_random_order`.

**How tested:**

- `python3 -m unittest -v`

**Next:** In-order traversal for `print` / `extract`; CSV `load`.

## Session 7 — `print`, `extract`, `load`

**Goal:** In-order walk of the B-tree for sorted output; `extract` writes `key,value` lines and must not overwrite; `load` parses CSV and reuses `insert_key`.

**What changed:**

- `btree_ops.all_pairs_inorder` / `_inorder_collect` (recursive in-order: child\(_i\), key\(_i\), …, last child).
- `project3.py`: `_cmd_print`, `_cmd_extract`, `_cmd_load` (strip lines, skip blanks, two comma-separated fields per row).
- `test_io_commands.py`: in-order list vs hand-built tree; subprocess tests for print order, extract→load roundtrip, extract clobber error, missing CSV.

**How tested:**

- `python3 -m unittest -v` — full suite (19 tests), including:
  - **`TestAllPairsInorder`:** build a 3-node index on disk (internal + two leaves), assert `all_pairs_inorder` returns `[(10,10), (50,500), (60,60)]`.
  - **`test_print_sorted_and_empty`:** subprocess `create` → empty `print` (no stdout) → three `insert`s out of order → `print` must emit keys sorted.
  - **`test_extract_and_load_roundtrip`:** `extract` to CSV, assert file contents are two lines `1,10` and `5,50`; new index + `load` from that file → `print` matches.
  - **`test_extract_refuses_existing_output`:** pre-create output path → `extract` fails → file contents unchanged.
  - **`test_load_missing_csv`:** `load` with nonexistent CSV exits non-zero.

**Next:** Final error-pass / README polish if needed; TA notes.

## Session 8 — Validation and error handling

**Goal:** Treat obviously broken files as invalid indexes before touching tree logic; surface corrupt reads clearly; drop dead CLI stub.

**What changed:**

- `is_valid_index_file`: require non-zero size, multiple of 512, `next_block_id == number of blocks`, and `root_id < next_block_id` when `root_id != 0`.
- `search` / `print` / `extract`: catch `ValueError` from block reads as `Error: corrupt index file: …` (in addition to `is_valid` gate for common cases).
- `project3.py`: removed `_stub`; unhandled subcommand is a `RuntimeError` (should not occur).
- `test_validation.py`: bad magic, wrong size, `next_id` vs file length, bogus root; CLI smoke test on bad magic.

**How tested:**

- `python3 -m unittest -v` (25 tests).

**Wrap-up:** All spec commands implemented; run the suite above before submission.
