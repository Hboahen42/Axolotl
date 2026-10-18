# Axolotl

A handwritten lexer, recursive-descent parser and tree-walking interpreter for the Axolotl language, following the grammar in [`docs/EBNF.txt`](docs/EBNF.txt). It turns source text into a stream of tokens, parses them into an Abstract Syntax Tree (AST), and then executes the AST, reporting detailed lexing, syntax or runtime errors (`errors`).

## Requirements

- Python 3.8+ (no third-party dependencies)

## Running Axolotl

`main.py` doubles as an interactive REPL, an automated test runner, and a file runner.

### Interactive REPL

Run without arguments to start the interactive prompt. Variables and functions persist between lines, and the value of a bare expression is echoed:

```bash
python main.py
```

```
Welcome to Axolotl 1.0 (type 'exit' to quit, 'debug' to toggle tokens/AST)
Axolotl > let x = 10 + 5 * (2 - 1)
Axolotl > print(x)
15
Axolotl > x * 2
30
```

- Type `exit` to quit the REPL.
- Type `debug` to toggle printing the tokens and AST before each line runs.
- Type `test` in the REPL to open the interactive test runner menu, allowing you to select and run test suites from `test/lexer/`, `test/parser/` or `test/interpreter/`.

### Running Files

Pass a `.axo` file as an argument to run it:

```bash
python main.py "test/interpreter/test1.axo"
```

Add `-d` / `--debug` to also print the tokens and AST:

```bash
python main.py --debug "test/parser/test6.axo"
```

### Running the Tests

```bash
python test/test_interpreter.py
```

### Python API

You can also use the lexer and parser programmatically in Python:

```python
import lexer.lexer as lexer
import parser.parser as parser

source = 'let x = 10 + 5'
tokens, error = lexer.run('<stdin>', source)
if error:
    print(error.as_string())
else:
    print('Tokens:', tokens)
    res = parser.Parser(tokens).parse()
    if res.error:
        print(res.error.as_string())
    else:
        print('AST:', res.node)

        import interpreter.interpreter as interpreter
        value, error = interpreter.run(res.node)
        if error:
            print(error.as_string())
```

## Language Features

Axolotl supports:

- **Data Types**: Integers, floats (`10`, `3.14`), strings with escape sequences (`"hello\nworld"`), and booleans (`true`, `false`). Functions that finish without `return` produce `null`.
- **Variables & Assignment**: Variable declarations (`let x = 5`) and reassignments (`x = 10`).
- **Operators**:
  - Arithmetic: `+`, `-`, `*`, `/`, `^` (right-associative power), `%`
  - Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Control Flow**:
  - Conditional blocks: `if (condition) { ... } else { ... }`
  - Loops: `while (condition) { ... }`
- **Functions**: Function declarations (`fun add(a, b) { return a + b }`) and calls (`add(1, 2)`).
- **Built-in Statements**: `print(expr)` and `return expr`.
- **Comments**: Line comments starting with `#`.

## Interpreter

`interpreter/interpreter.py` walks the AST produced by the parser and executes it. `Interpreter.visit` dispatches each node to a matching `visit_<NodeName>` method (e.g. `visit_WhileNode`), which evaluates its children and returns a value.

### Values

Axolotl values are stored as plain Python values: numbers are `int`/`float`, strings are `str`, booleans are `bool`, `null` is `None`, and functions are `Function` objects (name, parameters, body and the scope they were defined in). Integer division that comes out whole stays an integer (`10 / 2` → `5`, `7 / 2` → `3.5`).

### Environment / Symbol Table

Variables live in `SymbolTable` objects, each holding a `dict` from name to value plus a link to its `parent` table:

- The program starts with one global table.
- Every block (`{ ... }` of an `if`, `else` or `while` body) runs in a new child table, so variables declared inside a block disappear when it ends.
- Every function call gets a new table whose parent is the table the function was **defined** in, holding its parameters.

Storing and retrieving:

- `let x = ...` → `define`: always stores `x` in the **current** table (so it can shadow an outer `x`).
- `x` (reading) → `find`/`get`: looks in the current table, then its parent, and so on outwards; if no table has `x`, it is an *undefined variable* error.
- `x = ...` (assignment) → `assign`: finds the nearest table that already has `x` and updates it there; assigning to a never-declared variable is an error.

A `Context` wraps the current symbol table with the name of the running function and the position it was called from, which is used to print a traceback when a runtime error happens.

### Runtime Errors

Runtime errors (`RTError` in `errors/errors.py`) stop the program and print a traceback through every function call, the message, and the offending code:

```
Traceback (most recent call last):
  File test/interpreter/test7.axo, line 6, in <program>
  File test/interpreter/test7.axo, line 3, in divide
Runtime Error: Division by zero

    return a / b
               ^
```

Handled errors include:

- **Undefined variables**: reading, assigning to, or calling a name that was never declared.
- **Division by zero**: `/` or `%` by zero, and `0 ^` a negative number.
- **Invalid operations**: operators on the wrong types (`"a" + 1`, `true * 2`, `1 < "2"`, `-"a"`), non-boolean `if`/`while` conditions, calling something that is not a function, wrong number of arguments, `return` outside a function, and recursion that is too deep.

## Project Layout

- `lexer/`
  - `lexer.py` – lexical analyzer / tokenizer
- `parser/`
  - `parser.py` – recursive descent parser
  - `ast.py` – AST node definitions (`ProgramNode`, `VarDeclarationNode`, `BinOpNode`, etc.)
- `interpreter/`
  - `interpreter.py` – tree-walking interpreter, `SymbolTable` and `Context`
- `errors` – custom error classes (`IllegalCharError`, `ExpectedCharError`, `InvalidSyntaxError`, `RTError`)
- `main.py` – REPL, test selector, and file runner entry point
- `docs/EBNF.txt` – language grammar reference
- `test/`
  - `lexer/` – sample `.axo` test cases for lexical analysis
  - `parser/` – sample `.axo` test cases for syntax and AST parsing
  - `interpreter/` – sample `.axo` programs for execution and runtime errors
  - `test_interpreter.py` – automated interpreter tests
