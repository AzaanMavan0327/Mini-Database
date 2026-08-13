import unittest

from src.parser.tokenizer import tokenize, Token, TokenType


class TestTokenizer(unittest.TestCase):
    def test_tokenizes_select_star(self):
        tokens = tokenize("SELECT * FROM users")
        expected = [
            Token(TokenType.KEYWORD, "SELECT"),
            Token(TokenType.SYMBOL, "*"),
            Token(TokenType.KEYWORD, "FROM"),
            Token(TokenType.IDENTIFIER, "users"),
            Token(TokenType.EOF, None),
        ]
        self.assertEqual(tokens, expected)

    def test_keywords_are_case_insensitive(self):
        tokens = tokenize("select * from users")
        self.assertEqual(tokens[0], Token(TokenType.KEYWORD, "SELECT"))
        self.assertEqual(tokens[2], Token(TokenType.KEYWORD, "FROM"))

    def test_tokenizes_string_literal(self):
        tokens = tokenize("'hello world'")
        self.assertEqual(tokens[0], Token(TokenType.STRING, "hello world"))

    def test_tokenizes_negative_number(self):
        tokens = tokenize("-5")
        self.assertEqual(tokens[0], Token(TokenType.NUMBER, -5))

    def test_tokenizes_all_operators(self):
        tokens = tokenize("= != < > <= >=")
        operators = [t.value for t in tokens if t.type == TokenType.OPERATOR]
        self.assertEqual(operators, ["=", "!=", "<", ">", "<=", ">="])

    def test_tokenizes_insert_statement(self):
        tokens = tokenize("INSERT INTO t VALUES (1, 'hi')")
        expected = [
            Token(TokenType.KEYWORD, "INSERT"),
            Token(TokenType.KEYWORD, "INTO"),
            Token(TokenType.IDENTIFIER, "t"),
            Token(TokenType.KEYWORD, "VALUES"),
            Token(TokenType.SYMBOL, "("),
            Token(TokenType.NUMBER, 1),
            Token(TokenType.SYMBOL, ","),
            Token(TokenType.STRING, "hi"),
            Token(TokenType.SYMBOL, ")"),
            Token(TokenType.EOF, None),
        ]
        self.assertEqual(tokens, expected)

    def test_empty_string_literal(self):
        tokens = tokenize("''")
        self.assertEqual(tokens[0], Token(TokenType.STRING, ""))

    def test_extra_whitespace_is_ignored(self):
        tokens = tokenize("  SELECT   *   FROM   users  ")
        self.assertEqual(tokens[0], Token(TokenType.KEYWORD, "SELECT"))
        self.assertEqual(tokens[-1], Token(TokenType.EOF, None))

    def test_unexpected_character_raises_value_error(self):
        with self.assertRaises(ValueError):
            tokenize("SELECT * FROM users WHERE key = #5")

    def test_tokenizes_and_or_as_keywords(self):
        tokens = tokenize("key = 1 AND value = 'a' OR key = 2")
        keywords = [t.value for t in tokens if t.type == TokenType.KEYWORD]
        self.assertEqual(keywords, ["AND", "OR"])

    def test_and_or_are_case_insensitive(self):
        tokens = tokenize("key = 1 and key = 2 or key = 3")
        keywords = [t.value for t in tokens if t.type == TokenType.KEYWORD]
        self.assertEqual(keywords, ["AND", "OR"])


if __name__ == "__main__":
    unittest.main()
