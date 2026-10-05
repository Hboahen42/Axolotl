##########################################
# Nodes
##########################################

class ProgramNode:
    def __init__(self, statements, pos_start, pos_end):
        self.statements = statements

        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self) -> str:
        return '(program ' + ' '.join(repr(stmt) for stmt in self.statements) + ')'

class BlockNode:
    def __init__(self, statements, pos_start, pos_end):
        self.statements = statements

        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self) -> str:
        return '(block ' + ' '.join(repr(stmt) for stmt in self.statements) + ')'

class VarDeclarationNode:
    """<var_declaration> ::= "let" <identifier> "=" <expression>"""
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

    def __repr__(self) -> str:
        return f'(let {self.var_name_tok.value} = {self.value_node})'

class AssignmentNode:
    """<assignment_statement> ::= <identifier> "=" <expression>"""
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

    def __repr__(self) -> str:
        return f'(assign {self.var_name_tok.value} = {self.value_node})'

class PrintNode:
    """<print_statement> ::= "print" "(" <expression> ")"""
    def __init__(self, expr_node, pos_start, pos_end):
        self.expr_node = expr_node

        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self) -> str:
        return f'(print {self.expr_node})'

class IfNode:
    """<if_statement> ::= "if" "(" <expression> ")" <block>
                            [ "else" <block> ]"""
    def __init__(self, condition_node, then_block, else_block, pos_start):
        self.condition_node = condition_node
        self.then_block = then_block
        self.else_block = else_block

        self.pos_start = pos_start
        self.pos_end = (self.else_block or self.then_block).pos_end

    def __repr__(self) -> str:
        if self.else_block:
            return f'(if {self.condition_node} {self.then_block} else {self.else_block})'
        return f'(if {self.condition_node} {self.then_block})'

class WhileNode:
    """<while_statement> ::= "while" "(" <expression> ")" <block>"""
    def __init__(self, condition_node, body_node, pos_start):
        self.condition_node = condition_node
        self.body_node = body_node

        self.pos_start = pos_start
        self.pos_end = self.body_node.pos_end

    def __repr__(self) -> str:
        return f'(while {self.condition_node} {self.body_node})'

class FuncDefNode:
    """<function_definition> ::= "fun" [<identifier>] "(" [ <parameters> ] ")"
                            <block>"""
    def __init__(self, var_name_tok, params_name_toks, body_node, pos_start):
        self.var_name_tok = var_name_tok
        self.params_name_toks = params_name_toks
        self.body_node = body_node

        self.pos_start = pos_start
        self.pos_end = self.body_node.pos_end

    def __repr__(self) -> str:
        name = self.var_name_tok.value if self.var_name_tok else '<anonymous>'
        params = ', '.join(tok.value for tok in self.params_name_toks)
        return f'(fun {name}({params}) {self.body_node})'

class ReturnNode:
    """<return_statement> ::= "return" <expression>"""
    def __init__(self, expr_node, pos_start):
        self.expr_node = expr_node

        self.pos_start = pos_start
        self.pos_end = self.expr_node.pos_end

    def __repr__(self) -> str:
        return f'(return {self.expr_node})'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self) -> str:
        return f'({self.left_node} {self.op_tok} {self.right_node})'

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

        self.pos_start = self.op_tok.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self) -> str:
        return f'({self.op_tok} {self.node})'

class NumberNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self) -> str:
        return f'{self.tok.value}'

class BooleanNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self) -> str:
        return f'{self.tok.value}'

class StringNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self) -> str:
        return f'{self.tok.value!r}'

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

    def __repr__(self) -> str:
        return f'{self.var_name_tok.value}'

class CallNode:
    """<function-call> ::= <identifier> "(" [ <arguments> ] ")" """
    def __init__(self, var_name_tok, arg_nodes, pos_end):
        self.var_name_tok = var_name_tok
        self.arg_nodes = arg_nodes

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = pos_end

    def __repr__(self) -> str:
        args = ', '.join(repr(arg) for arg in self.arg_nodes)
        return f'(call {self.var_name_tok.value}({args}))'