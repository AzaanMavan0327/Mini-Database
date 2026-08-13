# MiniDB Architecture

This document explains how MiniDB's pieces fit together and why certain
design decisions were made. It's meant to be read after using the REPL a
bit, as a companion to the code rather than a replacement for it.

## Overview

MiniDB is built in layers, each one only aware of the layer directly below
it:

```
REPL (src/engine/repl.py)
  │
  ├── legacy commands: insert / get / delete / keys
  │     │
  │     ▼
  │   DiskStore (src/storage/disk_store.py)
  │
  └── SQL statements: SELECT / INSERT INTO
        │
        ▼
      Tokenizer → Parser → SQL Executor (src/parser/, src/engine/sql_executor.py)
        │
        ▼
      DiskStore (src/storage/disk_store.py)
        │
        ├── BTree (src/storage/btree.py)       - in-memory index: key -> page number
        └── Pager (src/storage/pager.py)        - reads/writes fixed-size pages
              │
              ▼
            Page encode/decode (src/storage/page.py)
              │
              ▼
            minidb.db (the file on disk)
```

Each layer has one job and doesn't reach past the layer below it. The SQL
executor never touches the `Pager` directly, for example - it only knows
about `DiskStore`'s `insert`/`get`/`delete`/`keys` interface. That's what
makes each layer testable on its own (see the parallel structure in
`tests/`).

## The storage format

Data lives in fixed-size 4096-byte pages inside `minidb.db`. Each page
holds exactly one row:

```
┌─────────┬──────────┬───────────────┬─────────────────────────┐
│ occupied│ key      │ value length  │ value (padded with      │
│ (1 byte)│ (8 bytes)│ (4 bytes)     │ zeros to fill the page)  │
└─────────┴──────────┴───────────────┴─────────────────────────┘
```

**Why one row per page, instead of packing multiple rows into a page?**
It's much simpler to implement correctly - there's no offset table, no
tracking free space within a page, no compaction logic. The tradeoff is
wasted disk space (a 5-byte value still consumes a full 4KB page). Real
databases pack many rows per page for exactly this reason; that would be
a reasonable next step if this project continued.

**Why fixed-size pages at all, instead of just writing rows one after
another?** Fixed-size pages mean any page can be located directly by
`page_number * PAGE_SIZE`, with no need to scan through the file to find
where a given row starts. That's the same reason real databases use
paged storage.

## The index: why a B-tree

`DiskStore` needs to answer "which page holds key K?" without scanning
every page in the file. A plain hash map (Python `dict`) would answer
that in O(1) - and earlier versions of this project used exactly that.

The B-tree replaced it for two reasons:

1. **Ordering.** A hash map has no concept of "the next key after this
   one." A B-tree keeps keys sorted, so `keys()` and `SELECT *` return
   rows in order for free, and range queries (`WHERE key > 10`) become
   possible in principle.
2. **It's the real technique.** SQLite, Postgres, and MySQL's InnoDB
   engine all use B-trees (or the closely related B+-tree) for exactly
   this job. Understanding how one works - especially the deletion
   logic, which has to rebalance the tree by borrowing keys from
   siblings or merging nodes - is most of the value of this project.

The index itself lives entirely in memory. On startup, `DiskStore` scans
every page once and rebuilds the B-tree from scratch (`_load_index` in
`disk_store.py`). This keeps the on-disk file format simple - it doesn't
need to encode the tree structure at all - at the cost of an O(n) startup
scan. For a learning project at this scale that tradeoff is fine; a
production database would persist the tree itself to avoid rescanning
gigabytes of data on every restart.

## The SQL layer

SQL text passes through three independent stages:

1. **Tokenizer** (`tokenizer.py`) turns a string like
   `"SELECT * FROM t WHERE key = 1"` into a flat list of tokens:
   `KEYWORD(SELECT)`, `SYMBOL(*)`, `KEYWORD(FROM)`, `IDENTIFIER(t)`, ...
   It knows nothing about SQL grammar - just how to chop text into
   meaningful pieces.

2. **Parser** (`parser.py`) is a hand-written recursive-descent parser.
   Each grammar rule gets its own method (`_parse_select`,
   `_parse_where`, `_parse_and_group`, `_parse_condition`), and each
   method consumes exactly the tokens it's responsible for, then hands
   control to the next method down. This is what makes `AND`/`OR`
   precedence work correctly: `_parse_where` handles `OR` by calling
   `_parse_and_group` repeatedly, and `_parse_and_group` handles `AND` by
   calling `_parse_condition` repeatedly. Because `AND` is parsed "one
   level deeper" than `OR`, it naturally binds tighter - the same idea as
   multiplication binding tighter than addition in arithmetic.

3. **Executor** (`sql_executor.py`) takes the parsed statement (a
   `SelectStatement` or `InsertStatement` - see `ast_nodes.py`) and runs
   it against `DiskStore`. A `WHERE` clause is represented as a list of
   AND-groups, OR'd together - `[[a, b], [c]]` means `(a AND b) OR c` -
   which makes evaluation a simple nested loop rather than a recursive
   tree walk.

**Known simplification:** `SELECT` always does a full scan (`store.keys()`
then `store.get()` for each one) and filters in Python, even for a query
like `WHERE key = 5` that the B-tree could answer directly with one
`search()` call. Teaching the executor to recognize equality/range
conditions on `key` and go straight to the B-tree instead of scanning
everything would be the natural next optimization.

## What's deliberately out of scope

A few things were left out on purpose, to keep the project focused
rather than because they'd be hard to add:

- **Multiple tables.** The table name in SQL is parsed but not enforced -
  there's only one implicit table (the whole store). Adding real tables
  would mean a schema/catalog layer and picking a storage layout per
  table.
- **`UPDATE` and `DELETE` in SQL.** `INSERT` already overwrites an
  existing key, which covers `UPDATE`'s job. Row removal still goes
  through the original `delete <key>` REPL command rather than SQL.
- **Parentheses in `WHERE`.** `AND`/`OR` precedence works, but there's no
  way to override it with `(...)` grouping.
- **Joins.** There's only one table, so there's nothing to join.

## A note on testing strategy

Each layer has its own test file that mirrors the source layout
(`test_btree.py` tests `btree.py`, `test_parser.py` tests `parser.py`,
and so on). Two testing techniques are worth calling out:

- **The B-tree fuzz test** (`test_btree.py`) runs hundreds of random
  insert/delete sequences and checks the tree agrees with a plain Python
  `dict` at every step. Hand-picked test cases are good at catching bugs
  you thought to look for; a fuzz test against a known-correct reference
  implementation is good at catching the ones you didn't.
- **Integration tests** (`test_sql_executor.py`) exercise the real
  `DiskStore` on a temp file rather than mocking it, including closing
  and reopening the store mid-test. That's what actually caught the
  first real bug in this project - `KeyError.__str__()` returning
  `repr()` output instead of the plain message - since it only showed up
  when running the REPL end-to-end, not in an isolated unit test.
