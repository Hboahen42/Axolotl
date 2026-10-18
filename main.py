import os
import re
import sys

import interpreter.interpreter as interpreter
import lexer.lexer as lexer
import parser.parser as parser


def run(fn, text, debug=False, context=None, show_result=False):
    """Lex, parse and execute `text`. With `debug`, also print the tokens and AST."""
    tokens, error = lexer.run(fn, text)
    if error:
        print(error.as_string())
        return 1

    if debug:
        print()
        print('Tokens:')
        print(tokens)

    res = parser.Parser(tokens).parse()
    if res.error:
        print(res.error.as_string())
        return 1

    if debug:
        print()
        print('AST:')
        print(res.node)
        print()
        print('Output:')

    value, error = interpreter.run(res.node, context)
    if error:
        print(error.as_string())
        return 1

    # In the REPL, echo the value of a bare expression like `1 + 2`
    if show_result and value is not None and res.node.statements             and not isinstance(res.node.statements[-1], parser.FuncDefNode):
        print(interpreter.to_display(value))
    return 0


def run_file(path, debug=False):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError as e:
        print(f'could not read {path}: {e}')
        return 1

    return run(path, text, debug)


def run_test_menu():
    try:
        category_input = input('Which test would you like to run? (lexer / parser / interpreter): ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not category_input or category_input in ('exit', 'quit', 'cancel', 'back', 'q'):
        return

    if category_input in ('lexer', 'lex', 'l', '1'):
        category = 'lexer'
    elif category_input in ('parser', 'parse', 'p', '2'):
        category = 'parser'
    elif category_input in ('interpreter', 'interpret', 'i', '3'):
        category = 'interpreter'
    else:
        print("Invalid option. Please choose 'lexer', 'parser' or 'interpreter'.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(base_dir, 'test', f'{category}')
    if not os.path.isdir(test_dir):
        test_dir = os.path.join('test', f'{category}')
    if not os.path.isdir(test_dir):
        print(f"Directory not found: {test_dir}")
        return

    files = [f for f in os.listdir(test_dir) if f.endswith('.axo')]
    files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

    if not files:
        print(f"No tests found for {category}.")
        return

    print(f"\nAvailable {category} tests:")
    for f in files:
        name = f[:-4] if f.endswith('.axo') else f
        print(f"  - {name}")

    try:
        choice = input(f"\nWhich test do you want to run? ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not choice or choice.lower() in ('exit', 'quit', 'cancel', 'back', 'q'):
        return

    target_file = None
    choice_normalized = choice.lower().replace(' ', '')
    for f in files:
        name = f[:-4] if f.endswith('.axo') else f
        if name.lower() in (choice_normalized, f"test{choice_normalized}") or f.lower() in (choice_normalized, f"{choice_normalized}.axo", f"test{choice_normalized}.axo"):
            target_file = f
            break

    if target_file is None:
        print(f"Test '{choice}' not found.")
        return

    test_path = os.path.join(test_dir, target_file)
    print(f"\n--- Running {category} test: {target_file} ---")
    # lexer/parser tests are about the tokens and AST, so show them too
    run_file(test_path, debug=category != 'interpreter')
    print()


def run_repl():
    print("Welcome to Axolotl 1.0 (type 'exit' to quit, 'debug' to toggle tokens/AST)")
    # one context for the whole session, so variables survive between lines
    context = interpreter.new_global_context()
    debug = False
    while True:
        try:
            text = input('Axolotl > ')
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if text.strip() == 'exit':
            return 0
        if text.strip().lower() == 'test':
            run_test_menu()
            continue
        if text.strip().lower() == 'debug':
            debug = not debug
            print(f"debug {'on' if debug else 'off'}")
            continue
        if not text.strip():
            continue

        run('<stdin>', text, debug, context, show_result=True)


def main():
    args = sys.argv[1:]
    debug = False
    if args and args[0] in ('-d', '--debug'):
        debug = True
        args = args[1:]

    if len(args) > 1:
        print('usage: python main.py [-d | --debug] [file.axo]')
        return 1
    if len(args) == 1:
        return run_file(args[0], debug)
    return run_repl()


if __name__ == '__main__':
    sys.exit(main())
