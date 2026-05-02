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

## Commands (planned)

| Command   | Summary                                      |
|----------|-----------------------------------------------|
| `create` | Create a new index file                       |
| `insert` | Insert a key/value pair                       |
| `search` | Look up a key                                 |
| `load`   | Insert pairs from a CSV file                  |
| `print`  | Print all key/value pairs to stdout           |
| `extract`| Write all pairs to a CSV file                 |

**Implemented so far:** `create`, `search`, `insert`, `print` (sorted key order), `extract` (CSV, refuses existing output), `load` (CSV bulk insert).

See `devlog.md` for session notes.

## Files

- `project3.py` — CLI entrypoint
- `index_file.py` — block size, endianness, header, raw block read/write helpers
- `btree_node.py` — node block layout (19 keys, 20 children), encode/decode
- `btree_ops.py` — `search_key` on an open index file
- `test_btree_node.py`, `test_btree_search.py`, `test_btree_insert.py`, `test_io_commands.py` — unittests (`python3 -m unittest -v`)
- `devlog.md` — design notes and session log

## Notes for the TA

- On-disk format and B-tree operations will follow the course spec (magic header, node layout, minimal degree 10, at most three nodes in memory at once).
