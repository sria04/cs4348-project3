#!/usr/bin/env python3
"""CS4348 Project 3 — B-tree index file CLI."""

from __future__ import annotations

import argparse
import os
import sys

import btree_ops
import index_file


def _stub(command: str) -> int:
    print(f"Command {command!r} is not implemented yet.", file=sys.stderr)
    return 1


def _cmd_create(path: str) -> int:
    try:
        index_file.create_index(path)
    except FileExistsError:
        print(f"Error: file already exists: {path}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: could not create index: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_search(path: str, key_text: str) -> int:
    if not index_file.is_valid_index_file(path):
        print("Error: invalid or missing index file", file=sys.stderr)
        return 1
    try:
        key = index_file.parse_uint64_key(key_text)
    except ValueError as e:
        print(f"Error: bad key: {e}", file=sys.stderr)
        return 1
    try:
        with open(path, "rb") as f:
            found = btree_ops.search_key(f, key)
    except OSError as e:
        print(f"Error: could not read index: {e}", file=sys.stderr)
        return 1
    if found is None:
        print("Error: key not found", file=sys.stderr)
        return 1
    k, v = found
    print(f"{k} {v}")
    return 0


def _cmd_insert(path: str, key_text: str, value_text: str) -> int:
    if not index_file.is_valid_index_file(path):
        print("Error: invalid or missing index file", file=sys.stderr)
        return 1
    try:
        key = index_file.parse_uint64_key(key_text)
        value = index_file.parse_uint64_key(value_text)
    except ValueError as e:
        print(f"Error: bad key or value: {e}", file=sys.stderr)
        return 1
    try:
        with open(path, "r+b") as f:
            btree_ops.insert_key(f, key, value)
    except btree_ops.DuplicateKeyError:
        print("Error: duplicate key", file=sys.stderr)
        return 1
    except btree_ops.LeafFullError:
        print("Error: leaf is full", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"Error: could not update index: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_print(path: str) -> int:
    if not index_file.is_valid_index_file(path):
        print("Error: invalid or missing index file", file=sys.stderr)
        return 1
    try:
        with open(path, "rb") as f:
            pairs = btree_ops.all_pairs_inorder(f)
    except OSError as e:
        print(f"Error: could not read index: {e}", file=sys.stderr)
        return 1
    for k, v in pairs:
        print(f"{k} {v}")
    return 0


def _cmd_extract(index_path: str, out_path: str) -> int:
    if not index_file.is_valid_index_file(index_path):
        print("Error: invalid or missing index file", file=sys.stderr)
        return 1
    if os.path.exists(out_path):
        print(f"Error: output file already exists: {out_path}", file=sys.stderr)
        return 1
    try:
        with open(index_path, "rb") as f:
            pairs = btree_ops.all_pairs_inorder(f)
        with open(out_path, "w", encoding="ascii", newline="\n") as out:
            for k, v in pairs:
                out.write(f"{k},{v}\n")
    except OSError as e:
        print(f"Error: could not write extract: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_load(index_path: str, csv_path: str) -> int:
    if not index_file.is_valid_index_file(index_path):
        print("Error: invalid or missing index file", file=sys.stderr)
        return 1
    if not os.path.isfile(csv_path):
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        return 1
    try:
        with open(csv_path, encoding="utf-8") as csvf:
            lines = csvf.readlines()
    except OSError as e:
        print(f"Error: could not read CSV: {e}", file=sys.stderr)
        return 1

    rows: list[tuple[int, int]] = []
    for lineno, line in enumerate(lines, start=1):
        s = line.strip()
        if not s:
            continue
        parts = s.split(",")
        if len(parts) != 2:
            print(f"Error: bad CSV line {lineno}: expected key,value", file=sys.stderr)
            return 1
        try:
            k = index_file.parse_uint64_key(parts[0].strip())
            v = index_file.parse_uint64_key(parts[1].strip())
        except ValueError as e:
            print(f"Error: bad number on line {lineno}: {e}", file=sys.stderr)
            return 1
        rows.append((k, v))

    try:
        with open(index_path, "r+b") as f:
            for k, v in rows:
                btree_ops.insert_key(f, k, v)
    except btree_ops.DuplicateKeyError:
        print("Error: duplicate key", file=sys.stderr)
        return 1
    except btree_ops.LeafFullError:
        print("Error: leaf is full", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"Error: could not update index: {e}", file=sys.stderr)
        return 1
    return 0


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
    if cmd == "create":
        return _cmd_create(args.index_file)
    if cmd == "search":
        return _cmd_search(args.index_file, args.key)
    if cmd == "insert":
        return _cmd_insert(args.index_file, args.key, args.value)
    if cmd == "print":
        return _cmd_print(args.index_file)
    if cmd == "extract":
        return _cmd_extract(args.index_file, args.output_file)
    if cmd == "load":
        return _cmd_load(args.index_file, args.csv_file)
    return _stub(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
