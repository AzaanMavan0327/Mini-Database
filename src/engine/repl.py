from src.storage.disk_store import DiskStore
from src.parser.parser import parse_sql, SQLSyntaxError
from src.engine.sql_executor import execute_statement

VALID_COMMANDS = ("insert", "get", "delete", "keys", "select", "exit")
DEFAULT_DB_FILE = "minidb.db"


def parse_command(raw_input):
    """Split a raw input line into a command and its arguments."""
    parts = raw_input.strip().split()
    if not parts:
        return None, []
    command = parts[0].lower()
    args = parts[1:]
    return command, args


def is_sql_statement(command, args):
    """SELECT ... and INSERT INTO ... are routed to the SQL parser.
    Plain 'insert <key> <value>' keeps using the original REPL command."""
    if command == "select":
        return True
    if command == "insert" and args and args[0].lower() == "into":
        return True
    return False


def handle_insert(store, args):
    if len(args) < 2:
        print("Error: insert requires a key and a value, e.g. 'insert 1 hello'")
        return

    key_str, value_parts = args[0], args[1:]
    try:
        key = int(key_str)
    except ValueError:
        print(f"Error: key must be an integer, got '{key_str}'")
        return

    value = " ".join(value_parts)
    store.insert(key, value)
    print(f"OK: inserted key {key}")


def handle_get(store, args):
    if len(args) != 1:
        print("Error: get requires exactly one key, e.g. 'get 1'")
        return

    try:
        key = int(args[0])
    except ValueError:
        print(f"Error: key must be an integer, got '{args[0]}'")
        return

    try:
        value = store.get(key)
        print(value)
    except KeyError as e:
        print(f"Error: {e.args[0]}")


def handle_delete(store, args):
    if len(args) != 1:
        print("Error: delete requires exactly one key, e.g. 'delete 1'")
        return

    try:
        key = int(args[0])
    except ValueError:
        print(f"Error: key must be an integer, got '{args[0]}'")
        return

    try:
        store.delete(key)
        print(f"OK: deleted key {key}")
    except KeyError as e:
        print(f"Error: {e.args[0]}")


def handle_keys(store, args):
    keys = store.keys()
    if not keys:
        print("(no keys stored)")
        return
    print(", ".join(str(key) for key in keys))


def print_rows(rows):
    if not rows:
        print("(0 rows)")
        return
    for key, value in rows:
        print(f"{key} | {value}")
    row_word = "row" if len(rows) == 1 else "rows"
    print(f"({len(rows)} {row_word})")


def handle_sql(store, raw_sql):
    try:
        statement = parse_sql(raw_sql)
    except SQLSyntaxError as e:
        print(f"SQL Error: {e}")
        return

    try:
        result = execute_statement(statement, store)
    except KeyError as e:
        print(f"Error: {e.args[0]}")
        return

    if result is None:
        print(f"OK: inserted key {statement.key}")
    else:
        print_rows(result)


def run_repl(db_file=DEFAULT_DB_FILE):
    store = DiskStore(db_file)
    print("MiniDB REPL - type 'exit' to quit")
    print(f"Using database file: {db_file}")
    print("Commands: insert <key> <value>, get <key>, delete <key>, keys")
    print("SQL: SELECT * FROM <table> [WHERE cond [AND|OR cond]...]")
    print("     INSERT INTO <table> VALUES (<key>, '<value>')")

    while True:
        raw_input_line = input("minidb> ")
        stripped = raw_input_line.strip()
        command, args = parse_command(raw_input_line)

        if command is None:
            continue
        if command == "exit":
            store.close()
            print("Goodbye")
            break
        elif is_sql_statement(command, args):
            handle_sql(store, stripped)
        elif command == "insert":
            handle_insert(store, args)
        elif command == "get":
            handle_get(store, args)
        elif command == "delete":
            handle_delete(store, args)
        elif command == "keys":
            handle_keys(store, args)
        else:
            print(f"Unknown command '{command}'. Valid commands: {', '.join(VALID_COMMANDS)}")


if __name__ == "__main__":
    run_repl()
