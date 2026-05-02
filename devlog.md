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
