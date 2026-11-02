import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import interpreter.interpreter as interpreter
import lexer.lexer as lexer
import parser.parser as parser


def execute(source, context=None):
    """Run Axolotl source. Returns (printed lines, value, runtime error)."""
    tokens, error = lexer.run('<test>', source)
    assert error is None, error.as_string()
    res = parser.Parser(tokens).parse()
    assert res.error is None, res.error.as_string()

    lines = []
    value, error = interpreter.run(res.node, context, output=lines.append)
    return lines, value, error


class InterpreterTests(unittest.TestCase):
    def assertPrints(self, source, *expected):
        lines, _, error = execute(source)
        self.assertIsNone(error, error and error.as_string())
        self.assertEqual(lines, list(expected))

    def assertRuntimeError(self, source, message):
        _, _, error = execute(source)
        self.assertIsNotNone(error, 'expected a runtime error')
        self.assertIn(message, error.details)

    # --- required features ---

    def test_variables(self):
        self.assertPrints('let x = 10 let y = x + 5 print(y)', '15')
        self.assertPrints('let x = 1 x = x + 1 print(x)', '2')

    def test_arithmetic_and_precedence(self):
        self.assertPrints('print(2 + 3 * 4)', '14')
        self.assertPrints('print((2 + 3) * 4)', '20')
        self.assertPrints('print(10 - 4 - 3)', '3')
        self.assertPrints('print(20 / 4 / 5)', '1')
        self.assertPrints('print(7 / 2)', '3.5')
        self.assertPrints('print(-2 * 3)', '-6')
        self.assertPrints('print(2 ^ 3 ^ 2)', '512')
        self.assertPrints('print(10 % 3)', '1')
        self.assertPrints('print(1.5 + 1)', '2.5')

    def test_comparisons(self):
        self.assertPrints('print(1 == 1) print(1 != 1) print(1 < 2) print(1 > 2) print(2 <= 2) print(1 >= 2)',
                          'true', 'false', 'true', 'false', 'true', 'false')
        self.assertPrints('print(1 == 1.0) print("a" == "a") print(1 == "1") print(true == 1)',
                          'true', 'true', 'false', 'false')
        self.assertPrints('print(1 + 1 == 2)', 'true')

    def test_if_else(self):
        program = 'if (x >= 10) { print(x) } else { print(0) }'
        self.assertPrints('let x = 10 ' + program, '10')
        self.assertPrints('let x = 3 ' + program, '0')
        self.assertPrints('if (false) { print(1) }')

    def test_while(self):
        self.assertPrints('let x = 1 while (x <= 5) { print(x) x = x + 1 }', '1', '2', '3', '4', '5')
        self.assertPrints('while (false) { print(1) }')

    # --- environment / symbol table ---

    def test_block_scope_shadowing(self):
        self.assertPrints('let x = 1 if (true) { let x = 2 print(x) } print(x)', '2', '1')

    def test_assignment_updates_enclosing_scope(self):
        self.assertPrints('let x = 1 if (true) { x = 2 } print(x)', '2')

    def test_block_variables_do_not_leak(self):
        self.assertRuntimeError('if (true) { let y = 1 } print(y)', "'y' is not defined")

    def test_context_persists_between_runs(self):
        context = interpreter.new_global_context()
        execute('let x = 41', context)
        lines, _, error = execute('print(x + 1)', context)
        self.assertIsNone(error)
        self.assertEqual(lines, ['42'])

    def test_functions(self):
        self.assertPrints('fun add(a, b) { return a + b } print(add(2, 3))', '5')
        self.assertPrints('fun f(n) { if (n <= 1) { return 1 } return n * f(n - 1) } print(f(10))', '3628800')
        self.assertPrints('fun noop() { let a = 1 } print(noop())', 'null')
        # functions see the scope they were defined in
        self.assertPrints('let base = 10 fun add_base(n) { return n + base } print(add_base(5))', '15')
        # parameters don't leak into the caller
        self.assertRuntimeError('fun f(p) { return p } f(1) print(p)', "'p' is not defined")

    # --- runtime errors ---

    def test_undefined_variable(self):
        self.assertRuntimeError('print(y)', "'y' is not defined")
        self.assertRuntimeError('y = 5', "Cannot assign to undefined variable 'y'")
        self.assertRuntimeError('undefined_fn()', "'undefined_fn' is not defined")

    def test_division_by_zero(self):
        self.assertRuntimeError('print(1 / 0)', 'Division by zero')
        self.assertRuntimeError('let z = 0 print(10 / (z * 5))', 'Division by zero')
        self.assertRuntimeError('print(1.5 / 0.0)', 'Division by zero')
        self.assertRuntimeError('print(1 % 0)', 'Modulo by zero')
        self.assertRuntimeError('print(0 ^ -1)', 'Cannot raise zero to a negative power')

    def test_invalid_operations(self):
        self.assertRuntimeError('print("a" + 1)', 'Invalid operation: string + number')
        self.assertRuntimeError('print("a" - "b")', 'Invalid operation: string - string')
        self.assertRuntimeError('print(true + 1)', 'Invalid operation: boolean + number')
        self.assertRuntimeError('print(1 < "2")', 'Invalid operation: number < string')
        self.assertRuntimeError('print(-"a")', 'Cannot negate a string')
        self.assertRuntimeError('if (1) { print(1) }', "'if' condition must be a boolean, got number")
        self.assertRuntimeError('while ("yes") { print(1) }', "'while' condition must be a boolean")
        self.assertRuntimeError('let x = 1 x()', "'x' is a number, not a function")
        self.assertRuntimeError('fun f(a) { return a } f(1, 2)', 'expects 1 argument(s) but got 2')
        self.assertRuntimeError('return 1', "'return' outside of a function")
        self.assertRuntimeError('fun f() { return f() } f()', 'Maximum recursion depth')

    def test_error_stops_execution(self):
        lines, _, error = execute('print(1) print(1 / 0) print(2)')
        self.assertIsNotNone(error)
        self.assertEqual(lines, ['1'])

    def test_traceback_through_calls(self):
        _, _, error = execute('fun divide(a, b) {\n return a / b\n}\nprint(divide(1, 0))')
        text = error.as_string()
        self.assertIn('in <program>', text)
        self.assertIn('in divide', text)

    def test_function_with_three_parameters(self):
        self.assertPrints(
            'fun add(a, b, c) { return a + b + c } print(add(10, 20, 30))',
            '60'
        )
    def test_function_called_multiple_times(self):
        self.assertPrints(
            'fun square(n) { return n * n } print(square(3)) print(square(5))',
            '9', '25'
        )

    def test_early_return(self):
        self.assertPrints(
            'fun check(n) { if (n > 0) { return 1 } return 0 } print(check(5))',
            '1'
        )

    def test_nested_function_calls(self):
        self.assertPrints(
            'fun double(n) { return n * 2 } print(double(double(3)))',
            '12'
        )

    def test_local_variable_isolation(self):
        self.assertPrints(
            'let x = 100 fun f() { let x = 50 return x } print(f()) print(x)',
            '50', '100'
        )

    # --- for loops (extension feature) ---

    def assertSyntaxError(self, source, message):
        tokens, error = lexer.run('<test>', source)
        self.assertIsNone(error, error and error.as_string())
        res = parser.Parser(tokens).parse()
        self.assertIsNotNone(res.error, 'expected a syntax error')
        self.assertIn(message, res.error.details)

    def test_for_loop_basic(self):
        self.assertPrints('for (let i = 0; i < 3; i = i + 1) { print(i) }', '0', '1', '2')
        self.assertPrints('let s = 0 for (let i = 1; i <= 100; i = i + 1) { s = s + i } print(s)', '5050')
        self.assertPrints('for (let i = 3; i > 0; i = i - 1) { print(i) }', '3', '2', '1')
        self.assertPrints('for (let i = 0; i <= 10; i = i + 5) { print(i) }', '0', '5', '10')

    def test_for_loop_body_never_runs(self):
        self.assertPrints('for (let i = 10; i < 5; i = i + 1) { print(i) }')

    def test_for_loop_nested(self):
        self.assertPrints(
            'for (let r = 1; r <= 2; r = r + 1) { for (let c = 1; c <= 2; c = c + 1) { print(r * c) } }',
            '1', '2', '2', '4'
        )

    def test_for_loop_variable_is_scoped_to_loop(self):
        self.assertRuntimeError('for (let i = 0; i < 1; i = i + 1) { } print(i)', "'i' is not defined")
        self.assertPrints('let x = 99 for (let x = 0; x < 2; x = x + 1) { print(x) } print(x)', '0', '1', '99')

    def test_for_loop_body_variables_do_not_leak(self):
        self.assertRuntimeError('for (let i = 0; i < 1; i = i + 1) { let inside = 1 } print(inside)',
                                "'inside' is not defined")

    def test_for_loop_with_existing_variable(self):
        # without 'let' the loop reuses the outer variable, which keeps its final value
        self.assertPrints('let j = 0 for (j = 0; j < 3; j = j + 1) { } print(j)', '3')

    def test_for_loop_inside_function(self):
        self.assertPrints(
            'fun fact(n) { let r = 1 for (let i = 2; i <= n; i = i + 1) { r = r * i } return r } print(fact(5))',
            '120'
        )
        # 'return' inside the loop ends both the loop and the function
        self.assertPrints(
            'fun first(limit) { for (let n = 1; n < 100; n = n + 1) { if (n * n > limit) { return n } } return -1 } '
            'print(first(50))',
            '8'
        )

    def test_for_loop_runtime_errors(self):
        self.assertRuntimeError('for (let i = 0; 5; i = i + 1) { }', "'for' condition must be a boolean, got number")
        self.assertRuntimeError('for (k = 0; k < 3; k = k + 1) { }', "Cannot assign to undefined variable 'k'")

    def test_for_loop_syntax_errors(self):
        self.assertSyntaxError('for let i = 0; i < 3; i = i + 1) { }', "Expected '(' after 'for'")
        self.assertSyntaxError('for (5; true; i = 1) { }', "Expected 'let' or an assignment")
        self.assertSyntaxError('for (let i = 0 i < 3; i = i + 1) { }', "Expected ';' after for loop initialization")
        self.assertSyntaxError('for (let i = 0; i < 3 i = i + 1) { }', "Expected ';' after for loop condition")
        self.assertSyntaxError('for (let i = 0; i < 3; i + 1) { }', "did you mean 'i = i + 1'?")
        self.assertSyntaxError('for (let i = 0; i < 3; 7) { }', 'Expected an assignment for the for loop increment')
        self.assertSyntaxError('for (let i = 0; i < 3; i = i + 1 { }', "Expected ')' after for loop increment")


if __name__ == '__main__':
    unittest.main()
