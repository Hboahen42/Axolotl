# Axolotl Lexer

A hand-written lexer (tokenizer) for the Axolotl language, following the
grammar in [`EBNF.txt`](EBNF.txt). It turns source text into a stream of
`Token` objects (integers, floats, strings, identifiers, keywords, operators,
punctuation) or reports a lexing error (`errors.py`).

## Requirements

- Python 3.8+ (no third-party dependencies)

## Running the lexer

`main.py` doubles as an interactive REPL and a file runner.

Run without arguments to get a prompt where you can type Axolotl source and
see the resulting tokens:

```bash
python main.py
```

```
Welcome to Axolotl 1.0
Axolotl > let x = 10 + 5 * (2 - 1)
[KEYWORD: let, IDENTIFIER: x, EQ, INTEGER: 10, PLUS, INTEGER: 5, MUL, LPAREN, INTEGER: 2, MINUS, INTEGER: 1, RPAREN, EOF]
```

Type `exit` to quit.

Or pass a `.axo` file to tokenize it directly:

```bash
python main.py test/test1.axo
```

You can also call the lexer directly from Python:

```python
import lexer

tokens, error = lexer.run('<stdin>', 'let x = 5')
if error:
    print(error.as_string())
else:
    print(tokens)
```

## Language features

The lexer recognizes:

- Numbers: integers and floats (`10`, `3.14`)
- Strings with escapes: `"hello\nworld"`
- Identifiers and keywords: `let`, `and`, `or`, `not`, `if`, `else`, `while`,
  `fun`, `return`, `print`, `true`, `false`
- Operators: `+ - * / ^ % = == != < > <= >=`
- Punctuation: `( ) { } ,`
- Line comments starting with `#`

## Project layout

- `lexer.py` – the tokenizer
- `errors.py` – error types (`IllegalCharError`, `ExpectedCharError`)
- `main.py` – REPL and file entry point
- `EBNF.txt` – grammar reference
- `test/` – sample `.axo` source files
