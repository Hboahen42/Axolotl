import sys

import lexer


def run_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError as e:
        print(f'could not read {path}: {e}')
        return 1

    tokens, error = lexer.run(path, text)

    if error:
        print(error.as_string())
        return 1

    for tok in tokens:
        print(tok)
    return 0


def run_repl():
    print("Welcome to Axolotl 1.0")
    while True:
        text = input('Axolotl > ')
        if (text == 'exit'):
            sys.exit(1)

        tokens, error = lexer.run('<stdin>', text)

        print(error.as_string() if error else tokens)

def main():
    if len(sys.argv) > 2:
        print('usage: python main.py [file.axo]')
        return 1
    if len(sys.argv) == 2:
        return run_file(sys.argv[1])
    return run_repl()


if __name__ == '__main__':
    sys.exit(main())