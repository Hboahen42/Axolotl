import string
from errors.errors import IllegalCharError, ExpectedCharError

##########################################
# TOKENS
##########################################
TT_INT = 'INTEGER'
TT_FLOAT = 'FLOAT'
TT_STRING = 'STRING'
TT_IDENTIFIER = 'IDENTIFIER'
TT_KEYWORD = 'KEYWORD'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_EXPO = 'EXPO'
TT_MOD = 'MOD'
TT_EQ = 'EQ'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_LCURLY = 'LCURLY'
TT_RCURLY = 'RCURLY'
TT_COMMA = 'COMMA'
TT_EE = 'EE'
TT_NE = 'NE'
TT_LT = 'LT'
TT_GT = 'GT'
TT_LTE = 'LTE'
TT_GTE = 'GTE'
TT_EOF = 'EOF'

KEYWORD = [
    'let',
    'and',
    'or',
    'not',
    'if',
    'else',
    'while',
    'fun',
    'return',
    'print',
    'true',
    'false',
]

COMMENT_CHAR = '#'

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self) -> str:
        if self.value is not None:
            return f'{self.type}: {self.value}'
        return f'{self.type}'

##########################################
# CONSTANTS
##########################################

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS + '_'

##########################################
# POSITION
##########################################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

###########################################
# LEXER
###########################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position (-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance (self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t\n\r':
                self.advance()
            elif self.current_char == COMMENT_CHAR:
                self.skip_comment()
            elif self.current_char in DIGITS:
                tok, error = self.make_number()
                if error: return [], error
                tokens.append(tok)
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tok, error = self.make_string()
                if error: return [], error
                tokens.append(tok)
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_EXPO, pos_start=self.pos))
                self.advance()
            elif self.current_char == '%':
                tokens.append(Token(TT_MOD, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token(TT_LCURLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TT_RCURLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                tok, error = self.make_not_equals()
                if error: return [], error
                tokens.append(tok)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        pos_start = tokens[-1].pos_end.copy() if tokens else self.pos
        tokens.append(Token(TT_EOF, pos_start=pos_start))
        return tokens, None

    def skip_comment(self):
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def make_number(self):
        has_dot = False
        num_str = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS:
            num_str += self.current_char
            self.advance()
        if self.current_char == '.':
            has_dot = True
            num_str += '.'
            self.advance()

            if self.current_char is not None and self.current_char not in DIGITS:
                return None, ExpectedCharError(pos_start, self.pos, "digit (after '.')")

            while self.current_char is not None and self.current_char in DIGITS:
                num_str += self.current_char
                self.advance()

        if has_dot:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos), None
        else:
            return Token(TT_INT, int(num_str), pos_start, self.pos), None

    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escaped = False
        self.advance()

        escape_characters = {
            'n': '\n',
            't': '\t',
            '"': '"',
            '\\': '\\',
        }

        while self.current_char is not None:
            if self.current_char == '\n':
                return None, ExpectedCharError(pos_start, self.pos, "closing '\"' before the end of the line")
            if escaped:
                if self.current_char not in escape_characters:
                    return None, ExpectedCharError(pos_start, self.pos, "valid escape character (n, t, \", \\)")
                string += escape_characters.get(self.current_char, self.current_char)
                escaped = False
            elif self.current_char == '\\':
                    escaped = True
            elif self.current_char == '"':
                self.advance()
                return Token(TT_STRING, string, pos_start, self.pos), None
            else:
                    string += self.current_char
            self.advance()

        return None, ExpectedCharError(pos_start, self.pos, "closing '\"' before the end of the file")


    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS:
            id_str += self.current_char
            self.advance()

        tok_type = TT_KEYWORD if id_str in KEYWORD else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!' )")

    def make_equals(self):
        tok_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        tok_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        tok_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error