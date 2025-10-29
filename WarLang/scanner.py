import re
from collections import namedtuple

# === TOKEN STRUCTURE ===
Token = namedtuple("Token", ["type", "value", "line", "column"])

# === KEYWORDS ===
KEYWORDS = {
    'battle': 'PROGRAM_START',
    'strategy': 'FUNCTION_DEFINITION',
    'soldier': 'INT_TYPE',
    'force': 'FLOAT_TYPE',
    'intel': 'STRING_TYPE',
    'flag': 'BOOL_TYPE',
    'shout': 'OUTPUT',
    'scout': 'INPUT',
    'shield': 'IF',
    'retreat': 'ELSE',
    'march': 'WHILE',
    'deploy': 'FOR',
    'victory': 'RETURN',
    '#call': 'INCLUDE_IMPORT',
    'camp': 'NAMESPACE'
}

# === TOKEN REGEX DEFINITIONS ===
PATTERNS = {
    'INCREMENT':    r'\+\+',        
    'DECREMENT':    r'--',          
    'NUMBER':       r'\d+(\.\d+)?',
    'STRING':       r'"[^"\n]*"?',
    'IDENTIFIER':   r'[A-Za-z_]\w*',
    'EQ':           r'==',
    'NOT_EQ':       r'!=',
    'LE':           r'<=',
    'GE':           r'>=',
    'ASSIGN':       r'=',
    'LESS_THAN':    r'<',
    'GREAT_THAN':   r'>',
    'PLUS':         r'\+',
    'MINUS':        r'-',
    'MUL':          r'\*',
    'DIV':          r'/',
    'LPAREN':       r'\(',
    'RPAREN':       r'\)',
    'LBRACE':       r'\{',
    'RBRACE':       r'\}',
    'SEMICOLON':    r';',
    'COMMENT':      r'\#.*',        
    'NEWLINE':      r'\n',
    'SKIP':         r'[ \t]+',
    'MISMATCH':     r'.'
}

def tokenize(code):
    line_num = 1
    line_start = 0
    tokens = []
    position = 0
    length = len(code)
    error_count = 0

    while position < length:
        match = None

        for name, pattern in PATTERNS.items():
            regex = re.compile(pattern)
            match = regex.match(code, position)

            if match:
                value = match.group()
                column = position - line_start + 1

                # === Handle newline ===
                if name == 'NEWLINE':
                    line_start = match.end()
                    line_num += 1
                    position = match.end()
                    break

                # === Skip whitespace/comments ===
                elif name in ('SKIP', 'COMMENT'):
                    position = match.end()
                    break

                # === STRING ===
                elif name == 'STRING':
                    if not value.endswith('"'):
                        print(f"[Lexical Error] Unterminated string literal at line {line_num}, column {column}")
                        error_count += 1
                    else:
                        tokens.append(Token(name, value, line_num, column))
                    position = match.end()
                    break

                # === NUMBER ===
                elif name == 'NUMBER':
                    next_pos = match.end()
                    # Check if invalid sequence like 123abc
                    if next_pos < length and re.match(r'[A-Za-z_]', code[next_pos]):
                        invalid_seq = re.match(r'\d+[A-Za-z_]\w*', code[position:]).group()
                        print(f"[Lexical Error] Invalid number format '{invalid_seq}' at line {line_num}, column {column}")
                        error_count += 1
                        position += len(invalid_seq)
                    else:
                        tokens.append(Token(name, value, line_num, column))
                        position = match.end()
                    break

                # === IDENTIFIER / KEYWORD ===
                elif name == 'IDENTIFIER':
                    token_type = KEYWORDS.get(value, 'IDENTIFIER')
                    tokens.append(Token(token_type, value, line_num, column))
                    position = match.end()
                    break

                # === INVALID '//' SEQUENCE ===
                elif name == 'DIV' and code[position:position+2] == '//':
                    print(f"[Lexical Error] Unexpected symbol '//' at line {line_num}, column {column}")
                    error_count += 1
                    position += 2
                    break

                # === INVALID CHARACTERS ===
                elif name == 'MISMATCH':
                    print(f"[Lexical Error] Unexpected symbol '{value}' at line {line_num}, column {column}")
                    error_count += 1
                    position = match.end()
                    break

                # === NORMAL TOKENS ===
                else:
                    tokens.append(Token(name, value, line_num, column))
                    position = match.end()
                    break

        if not match:
            error_char = code[position]
            print(f"[Lexical Error] Unexpected symbol '{error_char}' at line {line_num}, column {position - line_start + 1}")
            error_count += 1
            position += 1

    print(f"\nTokenization completed: {len(tokens)} tokens, {error_count} lexical error(s).")
    return tokens
