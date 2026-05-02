# CS4348 Project 3 — B-tree index files

Command-line tool that creates and manages on-disk B-tree index files (512-byte blocks, big-endian 64-bit integers). Course project for CS4348 (Spring 2026).

## Requirements

- Python 3.10+ (stdlib only)

## How to run

```bash
python3 project3.py <command> [arguments ...]
```

Use `--help` for global usage or per-command help, for example:

```bash
python3 project3.py --help
python3 project3.py create --help
```

## Commands

| Command   | Summary                                      |
|----------|-----------------------------------------------|
| `create` | Create a new index file                       |
| `insert` | Insert a key/value pair                       |
| `search` | Look up a key                                 |
| `load`   | Insert pairs from a CSV file                  |
| `print`  | Print all key/value pairs to stdout           |
| `extract`| Write all pairs to a CSV file                 |

All of the above are implemented. See `devlog.md` for session notes.

## Files

- `project3.py` — CLI entrypoint
- `index_file.py` — block size, endianness, header, raw block read/write helpers
- `btree_node.py` — node block layout (19 keys, 20 children), encode/decode
- `btree_ops.py` — search, insert (with splits), in-order collection
- `test_btree_node.py`, `test_btree_search.py`, `test_btree_insert.py`, `test_io_commands.py`, `test_validation.py` — unittests (`python3 -m unittest -v`)
- `devlog.md` — design notes and session log

## Notes for the TA

- **Format:** 512-byte blocks, magic `4348PRJ3`, big-endian unsigned 64-bit fields; header `root` / `next_block_id` must match file length (`next_block_id == file_size / 512`).
- **B-tree:** Minimal degree 10 (max 19 keys per node); insert uses CLRS-style split on the way down; parent pointers updated when internal children move.
- **Memory:** Search and insert paths decode one node at a time along the current step; split briefly reads parent + full child and writes back (within the spec’s cap).
- **Errors:** Invalid index (bad magic, size, header consistency) is rejected before commands run; traversal I/O problems surface as `Error: corrupt index file: …`.
