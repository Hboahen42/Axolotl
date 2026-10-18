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


if __name__ == '__main__':
    unittest.main()
