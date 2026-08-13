import unittest

from src.parser.parser import parse_sql, SQLSyntaxError
from src.parser.ast_nodes import SelectStatement, InsertStatement, Condition


class TestParser(unittest.TestCase):
    def test_parses_simple_select(self):
        statement = parse_sql("SELECT * FROM users")
        self.assertEqual(statement, SelectStatement(table_name="users", where=None))

    def test_parses_select_with_where_on_key(self):
        statement = parse_sql("SELECT * FROM users WHERE key = 1")
        expected = SelectStatement(
            table_name="users",
            where=[[Condition(column="key", operator="=", value=1)]],
        )
        self.assertEqual(statement, expected)

    def test_parses_select_with_where_on_value(self):
        statement = parse_sql("SELECT * FROM users WHERE value = 'Alice'")
        expected = SelectStatement(
            table_name="users",
            where=[[Condition(column="value", operator="=", value="Alice")]],
        )
        self.assertEqual(statement, expected)

    def test_parses_select_with_each_operator(self):
        for op in ["=", "!=", "<", ">", "<=", ">="]:
            statement = parse_sql(f"SELECT * FROM t WHERE key {op} 5")
            self.assertEqual(statement.where[0][0].operator, op)

    def test_column_name_is_case_insensitive(self):
        statement = parse_sql("SELECT * FROM t WHERE KEY = 1")
        self.assertEqual(statement.where[0][0].column, "key")

    def test_parses_insert_statement(self):
        statement = parse_sql("INSERT INTO users VALUES (1, 'Alice')")
        self.assertEqual(
            statement, InsertStatement(table_name="users", key=1, value="Alice")
        )

    def test_insert_with_negative_key(self):
        statement = parse_sql("INSERT INTO t VALUES (-5, 'x')")
        self.assertEqual(statement.key, -5)

    def test_statement_missing_select_or_insert_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("DELETE FROM users")

    def test_select_missing_star_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT FROM users")

    def test_select_missing_from_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * users")

    def test_where_with_unknown_column_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * FROM t WHERE age = 5")

    def test_where_missing_operator_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * FROM t WHERE key 5")

    def test_insert_missing_values_keyword_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("INSERT INTO t (1, 'x')")

    def test_insert_with_string_key_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("INSERT INTO t VALUES ('oops', 'x')")

    def test_insert_with_numeric_value_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("INSERT INTO t VALUES (1, 2)")

    def test_trailing_garbage_after_statement_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * FROM t WHERE key = 1 extra")

    def test_invalid_character_raises_sql_syntax_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * FROM t WHERE key = #5")

    # --- AND / OR tests ---

    def test_where_with_and_produces_single_group(self):
        statement = parse_sql("SELECT * FROM t WHERE key = 1 AND value = 'a'")
        expected_where = [[
            Condition(column="key", operator="=", value=1),
            Condition(column="value", operator="=", value="a"),
        ]]
        self.assertEqual(statement.where, expected_where)

    def test_where_with_or_produces_two_groups(self):
        statement = parse_sql("SELECT * FROM t WHERE key = 1 OR key = 2")
        expected_where = [
            [Condition(column="key", operator="=", value=1)],
            [Condition(column="key", operator="=", value=2)],
        ]
        self.assertEqual(statement.where, expected_where)

    def test_and_binds_tighter_than_or(self):
        # "a AND b OR c" should parse as "(a AND b) OR c"
        statement = parse_sql("SELECT * FROM t WHERE key = 1 AND value = 'a' OR key = 2")
        expected_where = [
            [
                Condition(column="key", operator="=", value=1),
                Condition(column="value", operator="=", value="a"),
            ],
            [Condition(column="key", operator="=", value=2)],
        ]
        self.assertEqual(statement.where, expected_where)

    def test_or_before_and_also_respects_precedence(self):
        # "a OR b AND c" should parse as "a OR (b AND c)"
        statement = parse_sql("SELECT * FROM t WHERE key = 1 OR key = 2 AND value = 'b'")
        expected_where = [
            [Condition(column="key", operator="=", value=1)],
            [
                Condition(column="key", operator="=", value=2),
                Condition(column="value", operator="=", value="b"),
            ],
        ]
        self.assertEqual(statement.where, expected_where)

    def test_where_ending_in_dangling_and_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * FROM t WHERE key = 1 AND")

    def test_where_ending_in_dangling_or_raises_error(self):
        with self.assertRaises(SQLSyntaxError):
            parse_sql("SELECT * FROM t WHERE key = 1 OR")


if __name__ == "__main__":
    unittest.main()
