# Axolotl

A handwritten lexer and recursive-descent parser for the Axolotl language, following the grammar in [`docs/EBNF.txt`](docs/EBNF.txt). It turns source text into a stream of tokens and parses them into an Abstract Syntax Tree (AST), reporting detailed syntax or lexing errors (`errors`).

## Requirements

- Python 3.8+ (no third-party dependencies)

## Running Axolotl

`main.py` doubles as an interactive REPL, an automated test runner, and a file runner.

### Interactive REPL

Run without arguments to start the interactive prompt:

```bash
python main.py
```

```
Welcome to Axolotl 1.0 (type 'exit' to quit)
Axolotl > let x = 10 + 5 * (2 - 1)
Tokens:
[KEYWORD: let, IDENTIFIER: x, EQ, INTEGER: 10, PLUS, INTEGER: 5, MUL, LPAREN, INTEGER: 2, MINUS, INTEGER: 1, RPAREN, EOF]
AST:
(program (let x = (10 PLUS (5 MUL (2 MINUS 1)))))
```

- Type `exit` to quit the REPL.
- Type `test` in the REPL to open the interactive test runner menu, allowing you to select and run test suites from `test/lexer/` or `test/parser/`.

### Running Files

Pass a `.axo` file as an argument to tokenize and parse it:

```bash
python main.py "test/parser/test1.axo"
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
```

## Language Features

Axolotl supports:

- **Data Types**: Integers, floats (`10`, `3.14`), strings with escape sequences (`"hello\nworld"`), and booleans (`true`, `false`).
- **Variables & Assignment**: Variable declarations (`let x = 5`) and reassignments (`x = 10`).
- **Operators**:
  - Arithmetic: `+`, `-`, `*`, `/`, `^` (right-associative power), `%`
  - Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
  - Logical: `and`, `or`, `not`
- **Control Flow**:
  - Conditional blocks: `if (condition) { ... } else { ... }`
  - Loops: `while (condition) { ... }`
- **Functions**: Function declarations (`fun add(a, b) { return a + b }`) and calls (`add(1, 2)`).
- **Built-in Statements**: `print(expr)` and `return expr`.
- **Comments**: Line comments starting with `#`.

## Project Layout

- `lexer/`
  - `lexer.py` – lexical analyzer / tokenizer
- `parser/`
  - `parser.py` – recursive descent parser
  - `ast.py` – AST node definitions (`ProgramNode`, `VarDeclarationNode`, `BinOpNode`, etc.)
- `errors` – custom error classes (`IllegalCharError`, `ExpectedCharError`, `InvalidSyntaxError`)
- `main.py` – REPL, test selector, and file runner entry point
- `docs/EBNF.txt` – language grammar reference
- `test/`
  - `lexer/` – sample `.axo` test cases for lexical analysis
  - `parser/` – sample `.axo` test cases for syntax and AST parsing
