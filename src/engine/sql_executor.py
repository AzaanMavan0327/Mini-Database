from src.parser.ast_nodes import SelectStatement, InsertStatement

COMPARISONS = {
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


def execute_statement(statement, store):
    """Run a parsed SQL statement against the store.

    Returns a list of (key, value) rows for SELECT, or None for INSERT.
    """
    if isinstance(statement, InsertStatement):
        store.insert(statement.key, statement.value)
        return None

    if isinstance(statement, SelectStatement):
        return _execute_select(statement, store)

    raise TypeError(f"Unsupported statement type: {type(statement).__name__}")


def _execute_select(statement, store):
    rows = [(key, store.get(key)) for key in store.keys()]

    if statement.where is None:
        return rows

    condition = statement.where
    compare = COMPARISONS[condition.operator]

    matching_rows = []
    for key, value in rows:
        row_value = key if condition.column == "key" else value
        if _row_matches(compare, row_value, condition.value):
            matching_rows.append((key, value))

    return matching_rows


def _row_matches(compare, row_value, condition_value):
    """Run the comparison, treating mismatched types (e.g. comparing a
    string value with '<' against a number) as a non-match instead of
    letting it crash the query."""
    try:
        return compare(row_value, condition_value)
    except TypeError:
        return False
