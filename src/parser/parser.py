from src.parser.tokenizer import tokenize, TokenType
from src.parser.ast_nodes import SelectStatement, InsertStatement, Condition

VALID_COLUMNS = ("key", "value")


class SQLSyntaxError(Exception):
    """Raised when the SQL parser encounters invalid syntax."""


class Parser:
    """A recursive-descent parser for a small subset of SQL.

    Supports:
        SELECT * FROM <table> [WHERE <condition> [(AND|OR) <condition>]...]
        INSERT INTO <table> VALUES (<key>, '<value>')

    AND binds tighter than OR, same as real SQL, so
    'key = 1 AND value = "a" OR key = 2' means
    '(key = 1 AND value = "a") OR key = 2'. Parentheses for explicit
    grouping aren't supported.

    The table name is required by the grammar but not enforced, since
    the storage layer currently only supports a single implicit table.
    """

    def __init__(self, tokens):
        self._tokens = tokens
        self._position = 0

    def parse(self):
        token = self._current()
        if token.type == TokenType.KEYWORD and token.value == "SELECT":
            statement = self._parse_select()
        elif token.type == TokenType.KEYWORD and token.value == "INSERT":
            statement = self._parse_insert()
        else:
            raise SQLSyntaxError(f"Expected SELECT or INSERT, got {token.value!r}")

        if self._current().type != TokenType.EOF:
            raise SQLSyntaxError(f"Unexpected token after statement: {self._current().value!r}")

        return statement

    def _parse_select(self):
        self._expect_keyword("SELECT")
        self._expect_symbol("*")
        self._expect_keyword("FROM")
        table_name = self._expect_type(TokenType.IDENTIFIER, "table name").value

        where = None
        if self._current().type == TokenType.KEYWORD and self._current().value == "WHERE":
            where = self._parse_where()

        return SelectStatement(table_name=table_name, where=where)

    def _parse_where(self):
        """Parse a WHERE clause into OR-of-AND-groups, so AND binds
        tighter than OR: 'a AND b OR c' becomes [[a, b], [c]]."""
        self._expect_keyword("WHERE")

        groups = [self._parse_and_group()]
        while self._current().type == TokenType.KEYWORD and self._current().value == "OR":
            self._advance()
            groups.append(self._parse_and_group())

        return groups

    def _parse_and_group(self):
        conditions = [self._parse_condition()]
        while self._current().type == TokenType.KEYWORD and self._current().value == "AND":
            self._advance()
            conditions.append(self._parse_condition())
        return conditions

    def _parse_condition(self):
        column_token = self._expect_type(TokenType.IDENTIFIER, "column name")
        column = column_token.value.lower()
        if column not in VALID_COLUMNS:
            raise SQLSyntaxError(f"Unknown column '{column}', expected 'key' or 'value'")

        operator_token = self._expect_type(TokenType.OPERATOR, "comparison operator")

        value_token = self._advance()
        if value_token.type not in (TokenType.NUMBER, TokenType.STRING):
            raise SQLSyntaxError(f"Expected a number or string literal, got {value_token.value!r}")

        return Condition(column=column, operator=operator_token.value, value=value_token.value)

    def _parse_insert(self):
        self._expect_keyword("INSERT")
        self._expect_keyword("INTO")
        table_name = self._expect_type(TokenType.IDENTIFIER, "table name").value
        self._expect_keyword("VALUES")
        self._expect_symbol("(")

        key_token = self._expect_type(TokenType.NUMBER, "integer key")
        self._expect_symbol(",")
        value_token = self._expect_type(TokenType.STRING, "string value")

        self._expect_symbol(")")

        return InsertStatement(table_name=table_name, key=key_token.value, value=value_token.value)

    # --- token stream helpers ---

    def _current(self):
        return self._tokens[self._position]

    def _advance(self):
        token = self._tokens[self._position]
        self._position += 1
        return token

    def _expect_keyword(self, keyword):
        token = self._advance()
        if token.type != TokenType.KEYWORD or token.value != keyword:
            raise SQLSyntaxError(f"Expected '{keyword}', got {token.value!r}")
        return token

    def _expect_symbol(self, symbol):
        token = self._advance()
        if token.type != TokenType.SYMBOL or token.value != symbol:
            raise SQLSyntaxError(f"Expected '{symbol}', got {token.value!r}")
        return token

    def _expect_type(self, token_type, description):
        token = self._advance()
        if token.type != token_type:
            raise SQLSyntaxError(f"Expected {description}, got {token.value!r}")
        return token


def parse_sql(sql):
    """Tokenize and parse a SQL string into a statement object."""
    try:
        tokens = tokenize(sql)
    except ValueError as e:
        raise SQLSyntaxError(str(e))
    return Parser(tokens).parse()