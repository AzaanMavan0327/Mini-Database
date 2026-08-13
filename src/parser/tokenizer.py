import re

KEYWORDS = {"SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "AND", "OR"}


class TokenType:
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    OPERATOR = "OPERATOR"
    SYMBOL = "SYMBOL"
    EOF = "EOF"


class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.type == other.type and self.value == other.value


TOKEN_PATTERN = re.compile(r"""
    \s*(?:
        (?P<STRING>'[^']*')
      | (?P<NUMBER>-?\d+)
      | (?P<OPERATOR><=|>=|!=|=|<|>)
      | (?P<SYMBOL>[(),*])
      | (?P<WORD>[A-Za-z_][A-Za-z0-9_]*)
    )
""", re.VERBOSE)


def tokenize(sql):
    """Convert a SQL string into a list of Tokens, ending with an EOF token."""
    sql = sql.strip()
    tokens = []
    position = 0

    while position < len(sql):
        match = TOKEN_PATTERN.match(sql, position)
        if not match:
            raise ValueError(f"Unexpected character at position {position}: '{sql[position]}'")

        position = match.end()

        if match.lastgroup == "STRING":
            tokens.append(Token(TokenType.STRING, match.group("STRING")[1:-1]))
        elif match.lastgroup == "NUMBER":
            tokens.append(Token(TokenType.NUMBER, int(match.group("NUMBER"))))
        elif match.lastgroup == "OPERATOR":
            tokens.append(Token(TokenType.OPERATOR, match.group("OPERATOR")))
        elif match.lastgroup == "SYMBOL":
            tokens.append(Token(TokenType.SYMBOL, match.group("SYMBOL")))
        elif match.lastgroup == "WORD":
            word = match.group("WORD")
            if word.upper() in KEYWORDS:
                tokens.append(Token(TokenType.KEYWORD, word.upper()))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, word))

    tokens.append(Token(TokenType.EOF, None))
    return tokens