# MiniDB

A simplified database engine built from scratch to understand how real
databases like SQLite work under the hood. This is a learning project built
in stages, starting with an in-memory store and eventually adding
persistence, indexing, and a small SQL parser.

## Current Status: Week 4 - SQL Parser

MiniDB now understands a small subset of SQL on top of everything from
Weeks 1-3. You can run `SELECT` (with an optional `WHERE`) and `INSERT`
statements directly, alongside the original REPL commands.

The store is treated as one implicit table with two columns: `key`
(integer) and `value` (string) - since that's what the underlying
key-value store already holds. The table name in your SQL is required by
the grammar (so it looks like real SQL) but isn't enforced yet, since
there's currently only one table.

### Supported commands

| Command | Example | Description |
|---|---|---|
| `insert <key> <value>` | `insert 1 hello world` | Insert or overwrite a key |
| `get <key>` | `get 1` | Retrieve the value for a key |
| `delete <key>` | `delete 1` | Remove a key |
| `keys` | `keys` | List all stored keys, in sorted order |
| `exit` | `exit` | Quit the REPL |

### Supported SQL

```sql
SELECT * FROM <table>
SELECT * FROM <table> WHERE key = 5
SELECT * FROM <table> WHERE value = 'Alice'
SELECT * FROM <table> WHERE key > 10
INSERT INTO <table> VALUES (5, 'Alice')
```

WHERE supports one condition on `key` or `value`, using `=`, `!=`, `<`,
`>`, `<=`, or `>=`. `AND`/`OR` and SQL `DELETE`/`UPDATE` aren't supported
yet - the existing `delete` command still handles removal.

Keys must be integers. Values can contain spaces (up to 4083 bytes) and,
for SQL `INSERT`, must be wrapped in single quotes.

### How storage works

Data is stored in fixed-size 4096-byte pages in a `minidb.db` file (created
automatically on first run). Each page holds one row: a 1-byte occupied
flag, an 8-byte key, a 4-byte value length, and the value itself, padded to
fill the page. Deleted rows are marked free and their page is reused on the
next insert instead of growing the file.

### How the index works

On startup, MiniDB scans the file once and builds a B-tree mapping each key
to its page number, so lookups and deletes are O(log n) and `keys` (and
`SELECT *`) come back in sorted order automatically.

### How SQL execution works

SQL text goes through three stages, each its own module:

1. **Tokenizer** (`src/parser/tokenizer.py`) - turns the raw string into a
   list of tokens (keywords, identifiers, numbers, strings, operators)
2. **Parser** (`src/parser/parser.py`) - a hand-written recursive-descent
   parser that turns tokens into a `SelectStatement` or `InsertStatement`
3. **Executor** (`src/engine/sql_executor.py`) - runs the parsed statement
   against the `DiskStore`. `SELECT` does a full scan over `keys()` and
   filters in Python; it doesn't yet use the B-tree's ordering to skip
   rows for range queries like `WHERE key > 10` - that'd be a nice
   future optimization, but isn't needed at this scale.

## Running it

Requires Python 3.8+, no external dependencies.

```bash
python main.py
```

Example session mixing the original commands with SQL:

```
MiniDB REPL - type 'exit' to quit
Using database file: minidb.db
Commands: insert <key> <value>, get <key>, delete <key>, keys
SQL: SELECT * FROM <table> [WHERE key|value <op> <literal>]
     INSERT INTO <table> VALUES (<key>, '<value>')
minidb> insert 1 legacy row
OK: inserted key 1
minidb> INSERT INTO users VALUES (2, 'Alice')
OK: inserted key 2
minidb> SELECT * FROM users
1 | legacy row
2 | Alice
(2 rows)
minidb> SELECT * FROM users WHERE key = 2
2 | Alice
(1 row)
minidb> exit
Goodbye
```

## Running the tests

```bash
python -m unittest discover tests -v
```

71 tests covering the in-memory store, page encoding/decoding, the B-tree
(splits, merges, and a randomized fuzz test against a plain dict), disk
persistence, and the SQL tokenizer, parser, and executor.

## Project structure

```
minidb/
├── main.py                     # entry point, launches the REPL
├── src/
│   ├── storage/
│   │   ├── memory_store.py     # MemoryStore: in-memory insert/get/delete
│   │   ├── page.py             # encode/decode a row into a fixed-size page
│   │   ├── pager.py            # reads/writes pages to a file by page number
│   │   ├── btree.py            # BTree: sorted index with insert/search/delete
│   │   └── disk_store.py       # DiskStore: page-backed store, indexed by BTree
│   ├── parser/
│   │   ├── tokenizer.py        # turns SQL text into tokens
│   │   ├── ast_nodes.py        # SelectStatement, InsertStatement, Condition
│   │   └── parser.py           # recursive-descent parser: tokens -> statement
│   └── engine/
│       ├── repl.py             # command parsing and REPL loop
│       └── sql_executor.py     # runs a parsed SQL statement against DiskStore
├── tests/
│   ├── test_memory_store.py
│   ├── test_page.py
│   ├── test_btree.py
│   ├── test_disk_store.py
│   ├── test_tokenizer.py
│   ├── test_parser.py
│   └── test_sql_executor.py
└── README.md
```

## Roadmap

- [x] Week 1: In-memory key-value store + REPL
- [x] Week 2: Persist data to disk using fixed-size pages
- [x] Week 3: B-tree index for fast, sorted lookups
- [x] Week 4: Small SQL parser (`SELECT`, `INSERT`, `WHERE`)
- [ ] Week 5-6: Tests, docs, polish
