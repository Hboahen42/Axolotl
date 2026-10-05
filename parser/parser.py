from lexer.lexer import *
from errors.errors import InvalidSyntaxError
from parser.ast import *

##########################################
# PARSE RESULT
##########################################

class ParseResult:
    def __init__(self) -> None:
        self.error = None
        self.node = None

    def register(self, res):
        if res.error: self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self

##########################################
# PARSER
##########################################

class Parser:
    def __init__(self, tokens):
        self.current_tok = None
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def peek(self, offset=1):
        idx = self.tok_idx + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def error(self, res, details):
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end, details
        ))

    def expect(self, res, tok_type, details):
        if self.current_tok.type != tok_type:
            self.error(res, details)
            return None

        tok = self.current_tok
        self.advance()
        return tok

    def parse(self):
        res = self.program()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, 'Expected a statement or end of file'))
        return res

    # <program> ::= { <statement> }
    def program(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        statements = []

        while self.current_tok.type != TT_EOF:
            statement = res.register(self.statement())
            if res.error: return res
            statements.append(statement)

        pos_end = statements[-1].pos_end if statements else self.current_tok.pos_end.copy()
        return res.success(ProgramNode(statements, pos_start, pos_end))

    # <block> ::= "{" { <statement> } "}"
    def block(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if not self.expect(res, TT_LCURLY, "Expected '{'"): return res

        statements = []
        while self.current_tok.type not in (TT_RCURLY, TT_EOF):
            statement = res.register(self.statement())
            if res.error: return res
            statements.append(statement)

        pos_end = self.current_tok.pos_end.copy()
        if not self.expect(res, TT_RCURLY, "Expected '}'"): return res

        return res.success(BlockNode(statements, pos_start, pos_end))

    # <statement> ::= <variable_declaration>
    #               | <assignment>
    #               | <print_statement>
    #               | <if_statement>
    #               | <while_statement>
    #               | <function_definition>
    #               | <return_statement>
    #               | <expression_statement>
    def statement(self):
        tok = self.current_tok

        if tok.matches(TT_KEYWORD, 'let'):
            return self.variable_declaration()
        if tok.matches(TT_KEYWORD, 'print'):
            return self.print_statement()
        if tok.matches(TT_KEYWORD, 'if'):
            return self.if_statement()
        if tok.matches(TT_KEYWORD, 'while'):
            return self.while_statement()
        if tok.matches(TT_KEYWORD, 'fun'):
            return self.function_definition()
        if tok.matches(TT_KEYWORD, 'return'):
            return self.return_statement()

        if tok.type == TT_IDENTIFIER and self.peek().type == TT_EQ:
            return self.assignment()

        return self.expression_statement()

    # <variable_declaration> ::= "let" <identifier> "=" <expression>
    def variable_declaration(self):
        res = ParseResult()
        self.advance()  # 'let'

        var_name_tok = self.expect(res, TT_IDENTIFIER, 'Expected an identifier')
        if not var_name_tok: return res

        if not self.expect(res, TT_EQ, "Expected '='"): return res

        value = res.register(self.expression())
        if res.error: return res

        return res.success(VarDeclarationNode(var_name_tok, value))

    # <assignment> ::= <identifier> "=" <expression>
    def assignment(self):
        res = ParseResult()
        var_name_tok = self.current_tok
        self.advance()  # identifier
        self.advance()  # '='

        value = res.register(self.expression())
        if res.error: return res

        return res.success(AssignmentNode(var_name_tok, value))

    # <print_statement> ::= "print" "(" <expression> ")"
    def print_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        if not self.expect(res, TT_LPAREN, "Expected '(' after 'print'"): return res

        expr = res.register(self.expression())
        if res.error: return res

        pos_end = self.current_tok.pos_end.copy()
        if not self.expect(res, TT_RPAREN, "Expected ')'"): return res

        return res.success(PrintNode(expr, pos_start, pos_end))

    # <if_statement> ::= "if" "(" <expression> ")" <block>
    #                    [ "else" <block> ]
    def if_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        if not self.expect(res, TT_LPAREN, "Expected '(' after 'if'"): return res

        condition = res.register(self.expression())
        if res.error: return res

        if not self.expect(res, TT_RPAREN, "Expected ')'"): return res

        then_block = res.register(self.block())
        if res.error: return res

        else_block = None
        if self.current_tok.matches(TT_KEYWORD, 'else'):
            self.advance()
            else_block = res.register(self.block())
            if res.error: return res

        return res.success(IfNode(condition, then_block, else_block, pos_start))

    # <while_statement> ::= "while" "(" <expression> ")" <block>
    def while_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        if not self.expect(res, TT_LPAREN, "Expected '(' after 'while'"): return res

        condition = res.register(self.expression())
        if res.error: return res

        if not self.expect(res, TT_RPAREN, "Expected ')'"): return res

        body = res.register(self.block())
        if res.error: return res

        return res.success(WhileNode(condition, body, pos_start))

    # <function_definition> ::= "fun" [<identifier>] "(" [ <parameters> ] ")"
    #                           <block>
    def function_definition(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        var_name_tok = None
        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            self.advance()

        details = "Expected '('" if var_name_tok else "Expected an identifier or '('"
        if not self.expect(res, TT_LPAREN, details): return res

        param_name_tok = []
        if self.current_tok.type == TT_IDENTIFIER:
            param_name_tok.append(self.current_tok)
            self.advance()

            while self.current_tok.type == TT_COMMA:
                self.advance()
                param_tok = self.expect(res, TT_IDENTIFIER, 'Expected an identifier')
                if not param_tok: return res
                param_name_tok.append(param_tok)

        if not self.expect(res, TT_RPAREN, "Expected ')'"): return res

        body = res.register(self.block())
        if res.error: return res

        return res.success(FuncDefNode(var_name_tok, param_name_tok, body,pos_start))

    # <return_statement> ::= "return" <expression>
    def return_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        expr = res.register(self.expression())
        if res.error: return res

        return res.success(ReturnNode(expr, pos_start))

    # <expression_statement> ::= <expression>
    def expression_statement(self):
        return self.expression()

    # <expression> ::= <comparison>
    def expression(self):
        return self.comparison()

    # <comparison> ::= <term>
    #                | <term> <comparison-operator> <term>
    def comparison(self):
        res = ParseResult()

        left = res.register(self.term())
        if res.error: return res

        if self.current_tok.type in (TT_EQ, TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE):
            op_tok = self.current_tok
            self.advance()

            right = res.register(self.term())
            if res.error: return res
            return res.success(BinOpNode(left, op_tok, right))

        return res.success(left)

    # <term> ::= <factor> { ("+" | "-") <factor> }
    def term(self):
        res = ParseResult()

        left = res.register(self.factor())
        if res.error: return res

        while self.current_tok.type in (TT_PLUS, TT_MINUS):
            op_tok = self.current_tok
            self.advance()

            right = res.register(self.factor())
            if res.error: return res

            left = BinOpNode(left, op_tok, right)

        return res.success(left)

    # <factor> ::= <unary> { ("*" | "/") <unary> }
    def factor(self):
        res = ParseResult()

        left = res.register(self.unary())
        if res.error: return res

        while self.current_tok.type in (TT_MUL, TT_DIV, TT_MOD):
            op_tok = self.current_tok
            self.advance()

            right = res.register(self.unary())
            if res.error: return res

            left = BinOpNode(left, op_tok, right)

        return res.success(left)

    # <unary> ::= [ "-" ] <primary>
    #             | <power>
    def unary(self):
        res = ParseResult()

        if self.current_tok.type == TT_MINUS:
            op_tok = self.current_tok
            self.advance()

            primary = res.register(self.primary())
            if res.error: return res

            return res.success(UnaryOpNode(op_tok, primary))

        return self.power()

    # <power> ::= <primary> [ "^" <unary> ]
    def power(self):
        res = ParseResult()
        left = res.register(self.primary())
        if res.error: return res

        if self.current_tok.type == TT_EXPO:
            op_tok = self.current_tok
            self.advance()

            right = res.register(self.unary())
            if res.error: return res

            return res.success(BinOpNode(left, op_tok, right))

        return res.success(left)

    # <primary> ::= <number>
    #             | <boolean>
    #             | <identifier>
    #             | <function-call>
    #             | "(" <expression> ")"
    def primary(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return res.success(NumberNode(tok))

        if tok.matches(TT_KEYWORD, 'true') or tok.matches(TT_KEYWORD, 'false'):
            self.advance()
            return res.success(BooleanNode(tok))

        if tok.type == TT_STRING:
            self.advance()
            return res.success(StringNode(tok))

        if tok.type == TT_IDENTIFIER:
            self.advance()
            if self.current_tok.type == TT_LPAREN:
                return self.function_call(tok)
            return res.success(VarAccessNode(tok))

        if tok.type == TT_LPAREN:
            self.advance()

            expr = res.register(self.expression())
            if res.error: return res

            if not self.expect(res, TT_RPAREN, "Expected ')'"): return res

            return res.success(expr)

        return self.error(res, "Expected a number, 'true', 'false', an identifier, '-', or '('")

    # <function-call> ::= <identifier> "(" [ <arguments> ] ")"
    # <arguments> ::= <expression> { "," <expression> }
    def function_call(self, var_name_tok):
        res = ParseResult()
        self.advance()

        arg_node = []
        if self.current_tok.type != TT_RPAREN:
            arg_node.append(res.register(self.expression()))
            if res.error: return res

            while self.current_tok.type == TT_COMMA:
                self.advance()
                arg_node.append(res.register(self.expression()))
                if res.error: return res

        pos_end = self.current_tok.pos_end.copy()
        if not self.expect(res, TT_RPAREN, "Expected ')'"): return res

        return res.success(CallNode(var_name_tok, arg_node, pos_end))

def run(fn, text):
    import lexer.lexer as lexer

    tokens, error = lexer.run(fn, text)
    if error: return None, error

    res = Parser(tokens).parse()
    return res.node, res.error