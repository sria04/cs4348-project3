#!/usr/bin/env python3
"""CS4348 Project 3 — B-tree index file CLI."""

from __future__ import annotations

import argparse
import sys


def _stub(command: str) -> int:
    print(f"Command {command!r} is not implemented yet.", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="project3",
        description="Create and manage 512-byte block B-tree index files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new index file.")
    p_create.add_argument("index_file", help="Path to the new .idx file.")

    p_insert = sub.add_parser("insert", help="Insert a key/value pair.")
    p_insert.add_argument("index_file")
    p_insert.add_argument("key")
    p_insert.add_argument("value")

    p_search = sub.add_parser("search", help="Look up a key.")
    p_search.add_argument("index_file")
    p_search.add_argument("key")

    p_load = sub.add_parser("load", help="Bulk insert from a CSV file.")
    p_load.add_argument("index_file")
    p_load.add_argument("csv_file")

    p_print = sub.add_parser("print", help="Print all key/value pairs.")
    p_print.add_argument("index_file")

    p_extract = sub.add_parser("extract", help="Write all pairs to a CSV file.")
    p_extract.add_argument("index_file")
    p_extract.add_argument("output_file")

    args = parser.parse_args(argv)
    cmd = args.command
    assert cmd is not None
    return _stub(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
