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

    return [(key, value) for key, value in rows if _row_matches_where(key, value, statement.where)]


def _row_matches_where(key, value, where_groups):
    """where_groups is a list of AND-groups, OR'd together: a row
    matches if it satisfies every condition in at least one group."""
    return any(
        all(_condition_matches(key, value, condition) for condition in group)
        for group in where_groups
    )


def _condition_matches(key, value, condition):
    row_value = key if condition.column == "key" else value
    compare = COMPARISONS[condition.operator]
    try:
        return compare(row_value, condition.value)
    except TypeError:
        # e.g. comparing a string value with '<' against a number -
        # treat as a non-match instead of crashing the query.
        return False