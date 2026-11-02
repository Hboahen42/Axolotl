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
  - Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=` (a single `=` inside an expression is also treated as `==`). Only one comparison is allowed per expression: `1 < 2 < 3` is a syntax error, so compare one pair at a time and use parentheses to combine results, e.g. `(1 < 2) == true`.
  - Negation: a single `-` before a value (`-5`, `-x`, `-(2 + 3)`). Two in a row (`--5`) is a syntax error; write `-(-5)` instead.
- **Control Flow**:
  - Conditional blocks: `if (condition) { ... } else { ... }`
  - Loops: `while (condition) { ... }` and `for (let i = 0; i < 5; i = i + 1) { ... }`
- **Functions**: Function declarations (`fun add(a, b) { return a + b }`) and calls (`add(1, 2)`).
- **Built-in Statements**: `print(expr)` and `return expr`.
- **Comments**: Line comments starting with `#`.

### Functions

Functions are declared with `fun`, take zero or more parameters, and return a value with `return`. A function that ends without `return` gives `null`. `return` must always be followed by a value: a bare `return` is a syntax error, so a function that should give nothing simply ends without `return`. Statements are not ended with `;` in Axolotl.

A name followed by `(` is a function call (`add(1, 2)`); a name on its own is a variable (`add`). The parser tells them apart by looking at the token after the name.

```
fun add(a, b) {
    return a + b
}
let result = add(10, 20)
print(result)        # 30
```

- **Definition**: `visit_FuncDefNode` creates a `Function` object (name, parameter names, body, and the symbol table it was defined in) and stores it under its name in the current scope.
- **Calls**: `visit_CallNode` looks the name up, checks it is a function and that the number of arguments matches, evaluates the arguments, and runs the body in a new scope that holds the parameters.
- **Return values**: `return` raises a `ReturnSignal` exception carrying the value; `visit_CallNode` catches it and uses the value as the result of the call. This lets `return` exit from anywhere in the body, including inside loops and `if` blocks.
- **Recursion** works because a function's name is defined before its body runs. The depth is capped at 500 calls, after which a runtime error is reported.

### Scope

Scope is a chain of `SymbolTable` objects (see [Environment / Symbol Table](#environment--symbol-table) below). The global table is created when the program starts. Each function call gets a new local table whose parent is the table the function was defined in, so:

```
let x = 10
fun test() {
    let x = 20       # stored in test's local table
    print(x)         # 20, found in the local table first
}
test()
print(x)             # 10, the global table was never changed
```

- `let` inside a function always creates a local variable, even if a global variable has the same name.
- Reading a name searches the local table first, then the outer tables up to the global table.
- `x = ...` without `let` updates the nearest existing `x`, so a function can change a global variable on purpose.
- Parameters and local variables disappear when the call ends.

### Extension Feature: `for` Loops

```
for (let i = 0; i < 5; i = i + 1) {
    print(i)
}
```

A `for` loop has three parts in its header, separated by `;`:

1. **Initialization**: a `let` declaration or an assignment, run once before the loop.
2. **Condition**: an expression that must be a boolean, checked before each pass.
3. **Increment**: an assignment, run after each pass.

How it was added:

- **Lexer**: `for` is a keyword, and `;` is a new `SEMI` token.
- **Parser**: `for_statement()` parses the header and body into a `ForNode` (`parser/ast.py`). It reports clear syntax errors, e.g. `for (let i = 0; i < 5; i + 1)` gives *Expected an assignment for the for loop increment (did you mean 'i = i + 1'?)*.
- **Interpreter**: `visit_ForNode` creates a new **loop scope**, runs the initialization in it, then repeats: check the condition, run the body, run the increment.

Loop scope:

- A variable declared with `let` in the header lives in the loop scope, so it does not exist after the loop and does not change an outer variable with the same name.
- The body is a block, so it gets its own fresh scope on every pass.
- The increment runs in the loop scope, so it updates the loop variable.
- If the initialization is an assignment (`for (i = 0; ...)`), the existing outer `i` is used and keeps its final value after the loop.

### Other Supported Features from the Extension List

`for` loops are our main extension. However, Axolotl also supports these other features from the assignment's list of extension options:

**Recursion.** A function can call itself, because its name is stored in the scope before the body runs. Each call gets its own local scope, so every level of recursion has its own copy of the parameters. Calls more than 500 deep stop with a *Maximum recursion depth* runtime error instead of crashing Python.

```
fun fib(n) {
    if (n < 2) {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}
print(fib(10))               # 55
```

**Strings.**
- String literals in double quotes, with the escape sequences `\n`, `\t`, `\"` and `\\`
- Joining strings with `+`: `"Hello, " + name`
- Repeating a string with `*` and a whole number: `"ab" * 3` → `ababab`
- Comparing strings with `==`, `!=`, `<`, `>`, `<=`, `>=`, where `<` and `>` compare alphabetically: `"apple" < "banana"` → `true`
- Clear errors for mixing types (`"a" + 1` → *Invalid operation: string + number*), invalid escape characters, and strings that are never closed

**Comments.** Everything from `#` to the end of the line is ignored by the lexer:

```
let x = 10    # this is a comment
```

**Additional data types.** Besides integers, Axolotl has:
- **floats** (`3.14`)
- **booleans** (`true`, `false`), which `if`, `while` and `for` conditions must be
- **`null`**, returned by a function that ends without `return`

Values of different types are never equal (`1 == "1"` → `false`, `true == 1` → `false`).

### New Tests

| File | What it tests |
|---|---|
| `test/interpreter/test9.axo` | Function definitions, parameters, calls, return values, early return, `null` result |
| `test/interpreter/test10.axo` | Global vs local scope, parameters, updating globals, local variables not visible outside (ends with an expected error) |
| `test/interpreter/test11.axo` | Basic `for` loops: counting up and down, steps, nested loops, `if` inside loops |
| `test/interpreter/test12.axo` | `for` loop scope (ends with an expected error) |
| `test/interpreter/test13.axo` | `for` loops combined with functions, including `return` from inside a loop |

`test/test_interpreter.py` also has unit tests for functions, scope, and `for` loops (including syntax and runtime errors).

## Interpreter

`interpreter/interpreter.py` walks the AST produced by the parser and executes it. `Interpreter.visit` dispatches each node to a matching `visit_<NodeName>` method (e.g. `visit_WhileNode`), which evaluates its children and returns a value.

### Values

Axolotl values are stored as plain Python values: numbers are `int`/`float`, strings are `str`, booleans are `bool`, `null` is `None`, and functions are `Function` objects (name, parameters, body and the scope they were defined in). Integer division that comes out whole stays an integer (`10 / 2` → `5`, `7 / 2` → `3.5`).

### Environment / Symbol Table

Variables live in `SymbolTable` objects, each holding a `dict` from name to value plus a link to its `parent` table:

- The program starts with one global table.
- Every block (`{ ... }` of an `if`, `else`, `while` or `for` body) runs in a new child table, so variables declared inside a block disappear when it ends.
- Every `for` loop gets a loop table around its body, holding the variable declared in its header.
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
- **Invalid operations**: operators on the wrong types (`"a" + 1`, `true * 2`, `1 < "2"`, `-"a"`), non-boolean `if`/`while`/`for` conditions, calling something that is not a function, wrong number of arguments, `return` outside a function, and recursion that is too deep.

## Project Layout

- `lexer/`
  - `lexer.py` – lexical analyzer / tokenizer
- `parser/`
  - `parser.py` – recursive descent parser
  - `ast.py` – AST node definitions (`ProgramNode`, `VarDeclarationNode`, `ForNode`, `FuncDefNode`, `CallNode`, etc.)
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
