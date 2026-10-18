import sys

from lexer.lexer import *
from errors.errors import RTError
from parser.ast import *

##########################################
# SYMBOL TABLE (ENVIRONMENT)
##########################################

class SymbolTable:
    """Maps variable names to their runtime values.

    Each scope (the program, a block, a function call) gets its own table,
    linked to the table of the scope that encloses it. Looking a name up
    walks outwards along these `parent` links until the name is found."""
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def find(self, name):
        """Return the table that holds `name`, or None if it is undefined."""
        table = self
        while table is not None:
            if name in table.symbols:
                return table
            table = table.parent
        return None

    def get(self, name):
        return self.find(name).symbols[name]

    def define(self, name, value):
        """`let` always creates the variable in the current scope."""
        self.symbols[name] = value

    def assign(self, name, value):
        """Plain `=` updates the nearest existing variable; returns False if there is none."""
        table = self.find(name)
        if table is None:
            return False
        table.symbols[name] = value
        return True

##########################################
# CONTEXT
##########################################

class Context:
    """Where code is currently running: which function (for tracebacks),
    which call site entered it, and which symbol table to use."""
    def __init__(self, display_name, symbol_table, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.symbol_table = symbol_table
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos

    def new_scope(self):
        """Same function, but a fresh nested scope (used for blocks)."""
        return Context(self.display_name, SymbolTable(self.symbol_table), self.parent, self.parent_entry_pos)

##########################################
# VALUES
##########################################
# Axolotl values are stored as plain Python values:
#   number  -> int / float     string -> str     boolean -> bool
#   null    -> None            function -> Function

class Function:
    def __init__(self, name, param_names, body_node, closure):
        self.name = name or '<anonymous>'
        self.param_names = param_names
        self.body_node = body_node
        self.closure = closure  # the symbol table the function was defined in

    def __repr__(self) -> str:
        return f'<function {self.name}>'

def is_number(value):
    # bool is a subclass of int in Python, but true/false are not numbers in Axolotl
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def type_name(value):
    if value is None: return 'null'
    if isinstance(value, bool): return 'boolean'
    if is_number(value): return 'number'
    if isinstance(value, str): return 'string'
    if isinstance(value, Function): return 'function'
    return type(value).__name__

def to_display(value):
    """How a value looks when printed."""
    if value is None: return 'null'
    if isinstance(value, bool): return 'true' if value else 'false'
    return str(value)

class ReturnSignal(Exception):
    """Unwinds the Python call stack from a `return` up to the function call."""
    def __init__(self, value):
        self.value = value

##########################################
# INTERPRETER
##########################################

OP_SYMBOLS = {
    TT_PLUS: '+', TT_MINUS: '-', TT_MUL: '*', TT_DIV: '/', TT_MOD: '%', TT_EXPO: '^',
    TT_EQ: '=', TT_EE: '==', TT_NE: '!=', TT_LT: '<', TT_GT: '>', TT_LTE: '<=', TT_GTE: '>=',
}

MAX_CALL_DEPTH = 500

# Each Axolotl call uses several Python frames (call -> block -> return -> expression ...),
# so give Python enough room to reach MAX_CALL_DEPTH before it gives up itself.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 30000))

class Interpreter:
    def __init__(self, output=print):
        self.output = output
        self.call_depth = 0

    def visit(self, node, context):
        method = getattr(self, f'visit_{type(node).__name__}', self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def error(self, node, details, context):
        return RTError(node.pos_start, node.pos_end, details, context)

    ###################################
    # Statements
    ###################################

    def visit_ProgramNode(self, node, context):
        value = None
        for statement in node.statements:
            value = self.visit(statement, context)
        return value

    def visit_BlockNode(self, node, context):
        block_context = context.new_scope()
        for statement in node.statements:
            self.visit(statement, block_context)
        return None

    def visit_VarDeclarationNode(self, node, context):
        value = self.visit(node.value_node, context)
        context.symbol_table.define(node.var_name_tok.value, value)
        return None

    def visit_AssignmentNode(self, node, context):
        name = node.var_name_tok.value
        value = self.visit(node.value_node, context)
        if not context.symbol_table.assign(name, value):
            raise RTError(node.var_name_tok.pos_start, node.var_name_tok.pos_end,
                          f"Cannot assign to undefined variable '{name}' (declare it first with 'let')", context)
        return None

    def visit_PrintNode(self, node, context):
        value = self.visit(node.expr_node, context)
        self.output(to_display(value))
        return None

    def visit_IfNode(self, node, context):
        if self.condition(node.condition_node, context, 'if'):
            self.visit(node.then_block, context)
        elif node.else_block:
            self.visit(node.else_block, context)
        return None

    def visit_WhileNode(self, node, context):
        while self.condition(node.condition_node, context, 'while'):
            self.visit(node.body_node, context)
        return None

    def condition(self, node, context, keyword):
        value = self.visit(node, context)
        if not isinstance(value, bool):
            raise self.error(node, f"'{keyword}' condition must be a boolean, got {type_name(value)}", context)
        return value

    def visit_FuncDefNode(self, node, context):
        name = node.var_name_tok.value if node.var_name_tok else None
        params = [tok.value for tok in node.params_name_toks]
        func = Function(name, params, node.body_node, context.symbol_table)
        if name:
            context.symbol_table.define(name, func)
        return func

    def visit_ReturnNode(self, node, context):
        if context.parent is None:
            raise self.error(node, "'return' outside of a function", context)
        raise ReturnSignal(self.visit(node.expr_node, context))

    ###################################
    # Expressions
    ###################################

    def visit_NumberNode(self, node, context):
        return node.tok.value

    def visit_StringNode(self, node, context):
        return node.tok.value

    def visit_BooleanNode(self, node, context):
        return node.tok.value == 'true'

    def visit_VarAccessNode(self, node, context):
        name = node.var_name_tok.value
        if context.symbol_table.find(name) is None:
            raise self.error(node, f"'{name}' is not defined", context)
        return context.symbol_table.get(name)

    def visit_UnaryOpNode(self, node, context):
        value = self.visit(node.node, context)
        if node.op_tok.type == TT_MINUS:
            if not is_number(value):
                raise self.error(node, f"Cannot negate a {type_name(value)}", context)
            return -value
        raise self.error(node, f"Unknown unary operator '{node.op_tok.type}'", context)

    def visit_BinOpNode(self, node, context):
        left = self.visit(node.left_node, context)
        right = self.visit(node.right_node, context)
        op = node.op_tok.type

        if op in (TT_EE, TT_EQ, TT_NE):
            equal = type_name(left) == type_name(right) and left == right
            return equal if op != TT_NE else not equal

        if op in (TT_LT, TT_GT, TT_LTE, TT_GTE):
            if not (is_number(left) and is_number(right)) and not (isinstance(left, str) and isinstance(right, str)):
                raise self.invalid_operation(node, left, right, context)
            if op == TT_LT: return left < right
            if op == TT_GT: return left > right
            if op == TT_LTE: return left <= right
            return left >= right

        if op == TT_PLUS:
            if is_number(left) and is_number(right): return left + right
            if isinstance(left, str) and isinstance(right, str): return left + right
            raise self.invalid_operation(node, left, right, context)

        if op == TT_MUL and isinstance(left, str) and is_number(right) and isinstance(right, int):
            return left * right

        if not (is_number(left) and is_number(right)):
            raise self.invalid_operation(node, left, right, context)

        if op == TT_MINUS: return left - right
        if op == TT_MUL: return left * right

        if op in (TT_DIV, TT_MOD):
            if right == 0:
                raise RTError(node.right_node.pos_start, node.right_node.pos_end,
                              'Division by zero' if op == TT_DIV else 'Modulo by zero', context)
            if op == TT_MOD: return left % right
            result = left / right
            # keep whole-number results of integer division as integers: 10 / 2 -> 5
            if isinstance(left, int) and isinstance(right, int) and result.is_integer():
                return int(result)
            return result

        if op == TT_EXPO:
            if left == 0 and right < 0:
                raise self.error(node, 'Cannot raise zero to a negative power', context)
            try:
                result = left ** right
            except OverflowError:
                raise self.error(node, 'Number too large', context)
            if isinstance(result, complex):
                raise self.error(node, 'Cannot raise a negative number to a fractional power', context)
            return result

        raise self.error(node, f"Unknown operator '{node.op_tok.type}'", context)

    def invalid_operation(self, node, left, right, context):
        return self.error(node, f"Invalid operation: {type_name(left)} {OP_SYMBOLS[node.op_tok.type]} {type_name(right)}", context)

    def visit_CallNode(self, node, context):
        name = node.var_name_tok.value
        if context.symbol_table.find(name) is None:
            raise RTError(node.var_name_tok.pos_start, node.var_name_tok.pos_end, f"'{name}' is not defined", context)

        func = context.symbol_table.get(name)
        if not isinstance(func, Function):
            raise self.error(node, f"'{name}' is a {type_name(func)}, not a function", context)

        args = [self.visit(arg, context) for arg in node.arg_nodes]
        if len(args) != len(func.param_names):
            raise self.error(node, f"'{func.name}' expects {len(func.param_names)} argument(s) but got {len(args)}", context)

        if self.call_depth >= MAX_CALL_DEPTH:
            raise self.error(node, f'Maximum recursion depth ({MAX_CALL_DEPTH}) exceeded', context)

        # The function body runs in a new scope whose parent is the scope the
        # function was *defined* in (its closure), not the scope it is called from.
        call_table = SymbolTable(func.closure)
        for param, arg in zip(func.param_names, args):
            call_table.define(param, arg)
        call_context = Context(func.name, call_table, context, node.pos_start)

        self.call_depth += 1
        try:
            self.visit(func.body_node, call_context)
        except ReturnSignal as ret:
            return ret.value
        finally:
            self.call_depth -= 1
        return None

##########################################
# RUN
##########################################

def new_global_context():
    return Context('<program>', SymbolTable())

def run(ast, context=None, output=print):
    """Execute an AST. Returns (value of the last statement, error)."""
    context = context or new_global_context()
    try:
        return Interpreter(output).visit(ast, context), None
    except RTError as error:
        return None, error
