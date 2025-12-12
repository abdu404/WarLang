from scanner import tokenize
import sys

# =========PARSE TREE NODE===========
class ParseNode:
    def __init__(self, name, children=None, value=None):
        self.name = name
        self.children = children if children else []
        self.value = value
        self.line = 0 

    def __repr__(self):
        return f"Node({self.name})"


# ===============PARSER==================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.errors = []

    # --- Helper functions for get the current token and move on to next and match if the expected found ---
    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return type('Token', (object,), {'type': 'EOF', 'value': '', 'line': -1})()

    def advance(self):
        if self.position < len(self.tokens):
            self.position += 1

    def match(self, expected_type):
        token = self.current_token()
        if token.type == expected_type:
            self.advance()
            return token
        else:
            self.error(f"Expected {expected_type} but found {token.type}")
            return None

    def error(self, message):
        token = self.current_token()
        err_msg = f"[Syntax Error] {message} at line {token.line}"
        self.errors.append(err_msg)
        
    # --- Node Helper ---
    def make_node(self, name, children=None, value=None, token=None):
        node = ParseNode(name, children, value)
        if token:
            node.line = token.line
        elif children and len(children) > 0:
             node.line = children[0].line
        elif self.position > 0:
             node.line = self.tokens[self.position-1].line
        return node

    
    #===========GRAMMAR IMPLEMENTATION==========
    def parse(self):
        root = self.make_node("Program")
        
        # 1. Imports
        imports = self.parse_import_list()
        if imports: root.children.append(imports)

        # 2. Global Declarations 
        globals_node = self.parse_global_decls()
        if globals_node: root.children.append(globals_node)

        # 3. Main Function
        main_func = self.parse_main_function()
        root.children.append(main_func)

        return root

    def parse_import_list(self):
        children = []
        # Checks for INCLUDE_IMPORT 
        while self.current_token().type == 'INCLUDE_IMPORT':
            children.append(self.parse_include_stmt())
        if not children: return None
        return self.make_node("ImportList", children)

    def parse_global_decls(self):
        children = []
        # Parses variables defined before 'battle'
        while self.current_token().type in ('INT_TYPE', 'FLOAT_TYPE', 'STRING_TYPE', 'BOOL_TYPE'):
            decl = self.parse_declaration()
            children.append(decl)

        if not children:
            return None
        return self.make_node("GlobalDeclarations", children)

    def parse_main_function(self):
        children = []
        if not self.match('PROGRAM_START'):
            return self.make_node("Error_Main")
        self.match('LPAREN')
        self.match('RPAREN')
        children.append(self.parse_block())
        return self.make_node("MainFunction", children)

    def parse_block(self):
        children = []
        self.match('LBRACE')
        children.append(self.parse_statement_list())
        self.match('RBRACE')
        return self.make_node("Block", children)

    def parse_statement_list(self):
        children = []
        while self.current_token().type not in ('RBRACE', 'EOF'):
            stmt = self.parse_statement()
            if stmt: children.append(stmt)
        return self.make_node("StatementList", children)

    def parse_statement(self):
        token = self.current_token()
        
        if token.type in ('INT_TYPE', 'FLOAT_TYPE', 'STRING_TYPE', 'BOOL_TYPE'):
            return self.parse_declaration()
        elif token.type == 'IDENTIFIER':
            return self.parse_assignment()
        elif token.type == 'IF':
            return self.parse_if_stmt()
        elif token.type == 'WHILE':
            return self.parse_while_stmt()
        elif token.type == 'FOR':
            return self.parse_for_stmt()
        elif token.type == 'OUTPUT':
            return self.parse_output_stmt()
        elif token.type == 'INPUT':
            return self.parse_input_stmt()
        elif token.type == 'COMMENT':
            self.advance()
            return None
        else:
            self.error(f"Unexpected token {token.type}")
            self.advance()
            return None

    def parse_declaration(self):
        children = []
        type_tok = self.current_token()
        self.advance()
        children.append(self.make_node("Type", value=type_tok.value, token=type_tok))

        id_tok = self.match('IDENTIFIER')
        if not id_tok: return None 
        children.append(self.make_node("Identifier", value=id_tok.value, token=id_tok))

        if self.current_token().type == 'ASSIGN':
            self.advance()
            children.append(self.make_node("AssignOp", value="="))
            children.append(self.parse_expr())

        self.match('SEMICOLON')
        return self.make_node("Declaration", children)

    def parse_assignment(self):
        children = []
        id_tok = self.match('IDENTIFIER')
        children.append(self.make_node("Identifier", value=id_tok.value, token=id_tok))
        
        self.match('ASSIGN')
        children.append(self.make_node("AssignOp", value="="))
        
        children.append(self.parse_expr())
        self.match('SEMICOLON')
        return self.make_node("Assignment", children)

    def parse_if_stmt(self):
        children = []
        self.match('IF')
        self.match('LPAREN')
        children.append(self.parse_expr())
        self.match('RPAREN')
        children.append(self.parse_block())
        
        if self.current_token().type == 'ELSE':
            self.match('ELSE')
            children.append(self.make_node("ElsePart", [self.parse_block()]))
            
        return self.make_node("IfStmt", children)

    def parse_while_stmt(self):
        children = []
        self.match('WHILE')
        self.match('LPAREN')
        children.append(self.parse_expr())
        self.match('RPAREN')
        children.append(self.parse_block())
        return self.make_node("WhileStmt", children)

    def parse_for_stmt(self):
        children = []
        self.match('FOR')
        self.match('LPAREN')
        
        if self.current_token().type in ('INT_TYPE', 'FLOAT_TYPE', 'STRING_TYPE', 'BOOL_TYPE'):
            children.append(self.parse_declaration())
        else:
             pass 

        children.append(self.parse_expr()) 
        self.match('SEMICOLON')
        children.append(self.parse_for_update()) 
        self.match('RPAREN')
        children.append(self.parse_block())
        return self.make_node("ForStmt", children)

    def parse_for_update(self):
        token = self.current_token()
        if token.type == 'IDENTIFIER':
            if self.tokens[self.position+1].type == 'ASSIGN':
                id_node = self.make_node("Identifier", value=token.value, token=token)
                self.advance(); self.advance()
                expr = self.parse_expr()
                return self.make_node("Assignment", [id_node, self.make_node("AssignOp", value="="), expr])
            elif self.tokens[self.position+1].type == 'INCREMENT':
                self.advance(); self.advance()
                return self.make_node("Increment", value=f"{token.value}++")
        return self.make_node("EmptyUpdate")

    def parse_output_stmt(self):
        children = []
        self.match('OUTPUT')
        self.match('LPAREN')
        children.append(self.parse_expr())
        while self.current_token().type == 'COMMA':
            self.advance()
            children.append(self.parse_expr())
        self.match('RPAREN')
        self.match('SEMICOLON')
        return self.make_node("OutputStmt", children)

    def parse_input_stmt(self):
        children = []
        self.match('INPUT')
        self.match('LPAREN')
        id_tok = self.match('IDENTIFIER')
        if id_tok:
             children.append(self.make_node("Identifier", value=id_tok.value, token=id_tok))
        self.match('RPAREN')
        self.match('SEMICOLON')
        return self.make_node("InputStmt", children)

    def parse_include_stmt(self):
        children = []
        self.match('INCLUDE_IMPORT')
        id_tok = self.match('IDENTIFIER')
        if id_tok:
             children.append(self.make_node("ImportName", value=id_tok.value))
        return self.make_node("IncludeStmt", children)

    # --- Expressions ---
    def parse_expr(self):
        return self.parse_relational()

    def parse_relational(self):
        node = self.parse_additive()
        while self.current_token().type in ('EQ', 'NOT_EQ', 'LESS_THAN', 'GREAT_THAN', 'LE', 'GE'):
            op = self.current_token()
            self.advance()
            right = self.parse_additive()
            node = self.make_node("RelationalExpr", [node, self.make_node("Op", value=op.value), right])
        return node

    def parse_additive(self):
        node = self.parse_term()
        while self.current_token().type in ('PLUS', 'MINUS'):
            op = self.current_token()
            self.advance()
            right = self.parse_term()
            node = self.make_node("AdditiveExpr", [node, self.make_node("Op", value=op.value), right])
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current_token().type in ('MUL', 'DIV'):
            op = self.current_token()
            self.advance()
            right = self.parse_factor()
            node = self.make_node("TermExpr", [node, self.make_node("Op", value=op.value), right])
        return node

    def parse_factor(self):
        token = self.current_token()
        if token.type == 'NUMBER':
            self.advance()
            return self.make_node("Number", value=token.value, token=token)
        elif token.type == 'STRING':
            self.advance()
            return self.make_node("String", value=token.value, token=token)
        elif token.type == 'IDENTIFIER':
            self.advance()
            return self.make_node("Identifier", value=token.value, token=token)
        elif token.type == 'BOOL_TYPE':
            self.advance()
            return self.make_node("Bool", value=token.value, token=token)
        elif token.type == 'LPAREN':
            self.advance()
            node = self.parse_expr()
            self.match('RPAREN')
            return node
        
        self.advance()
        return self.make_node("Error")
    
    def lookahead(self, offset=1):
        if self.position + offset < len(self.tokens):
            return self.tokens[self.position + offset]
        return None

    def print_tree(self, node, level=0):
        indent = "  " * level
        val = f": {node.value}" if node.value else ""
        print(f"{indent}{node.name}{val}")
        for child in node.children:
            self.print_tree(child, level + 1)
            