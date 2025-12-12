class SymbolTable:
    def __init__(self):
        # Stack of scopes. 
        # Each entry: {'type': 'soldier', 'line': 1, 'initialized': False}
        self.scopes = [] 
        self.enter_scope() # Global scope

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if self.scopes:
            self.scopes.pop()

    def add(self, name, data_type, line, initialized=False):
        current_scope = self.scopes[-1] # -1 means the top item
        # Check for redeclaration in CURRENT scope only
        if name in current_scope:
            return False # Error: Redeclared in same scope
        
        current_scope[name] = {'type': data_type, 'line': line, 'initialized': initialized}
        return True

    def lookup(self, name):
        # Search Top -> Bottom
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def mark_initialized(self, name): #This function is important for preventing the warning: "Variable used but not initialized."
        #the steps of the logic below 
        #1. Search Top -> Bottom (why we do the search again bcuz might be assigning to a global while inside a local loop.
        #2. this loop ensures we find the nearest visible variable and flip its switch to True.)
        for scope in reversed(self.scopes): 
            if name in scope:               # 2. Found the initialized variable?
                scope[name]['initialized'] = True # 3. UPDATE the value!
                return True
        return False
        
    def print_table_stack(self):
        for i, scope in enumerate(reversed(self.scopes)):
            level = len(self.scopes) - 1 - i 
            label = "GLOBAL SCOPE (Bottom)" if level == 0 else f"LOCAL SCOPE (Level {level})"
            print(f"\n   🔻 {label}")
            print("   " + "─" * 60)
            print(f"   | {'Variable Name':<15} | {'Type':<10} | {'Init?':<6} | {'Line':<5} |")
            print("   " + "─" * 60)
            for name, info in scope.items():
                init_str = "Yes" if info['initialized'] else "No"
                print(f"   | {name:<15} | {info['type']:<10} | {init_str:<6} | {str(info['line']):<5} |")
            print("   " + "─" * 60)

# the core function of it is : The Analyzer walking through the Parse Tree node by node.
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.warnings = []

    def log_error(self, message, line):
        self.errors.append(f"[Semantic Error] {message} at line {line}")

    def log_warning(self, message, line):
        self.warnings.append(f"[Semantic Warning] {message} at line {line}")

    def analyze(self, node): # the beginging 
        self.visit(node)

    def visit(self, node): 
        # It looks at the node's name and dynamically finds the matching function 
        # if not it calls visit_children() to keep digging deeper.
        method_name = f'visit_{node.name}'
        visitor = getattr(self, method_name, self.visit_children)
        return visitor(node)

    def visit_children(self, node):
        for child in node.children:
            self.visit(child)

    # --- Program Structure ---
    def visit_Program(self, node):
        self.visit_children(node)

    def visit_MainFunction(self, node):
        self.visit_children(node)
        
    def visit_Block(self, node):
        # Push Scope for Block
        # When entering a { } block, it calls self.symbol_table.enter_scope()
        # Exception: If this block is the MainFunction body, we might not want a new scope 
        # if we consider Global vars to be inside it. 
        self.symbol_table.enter_scope()
        self.visit_children(node)
        self.symbol_table.exit_scope()

    # --- Declarations ---
    def visit_Declaration(self, node):
        # Extracts Info 
        # Children: Type, Identifier, [AssignOp, Expr]
        # Type Check
        type_node = node.children[0]
        id_node = node.children[1]
        
        var_type = type_node.value
        var_name = id_node.value
        line = node.line
        
        is_initialized = False
        
        # Check optional assignment
        if len(node.children) > 2:
            expr_node = node.children[3]
            expr_type = self.visit(expr_node)
            is_initialized = True
            
            # TYPE CHECKING: Declaration Assignment
            self.check_assignment_compatibility(var_type, expr_type, line)

        # Add to Symbol Table
        success = self.symbol_table.add(var_name, var_type, line, is_initialized)
        if not success:
            self.log_error(f"Variable '{var_name}' already declared in this scope", line)

    # --- Assignments ---
    def visit_Assignment(self, node):
        # Checks if the variable exists. If not -> Error.
        # Children: Identifier, AssignOp, Expr
        id_node = node.children[0]
        var_name = id_node.value
        line = node.line
        
        # 1. Check if declared
        var_info = self.symbol_table.lookup(var_name)
        if not var_info:
            self.log_error(f"Variable '{var_name}' not declared", line)
            return
        
        # 2. Check Expression Type
        expr_node = node.children[2]
        expr_type = self.visit(expr_node)
        
        # 3. Check Compatibility
        self.check_assignment_compatibility(var_info['type'], expr_type, line)
        
        # 4. Mark Initialized is init or not 
        self.symbol_table.mark_initialized(var_name)

    # --- Control Flow ---
    def visit_IfStmt(self, node):
        # Check Condition is Boolean? (Optional, C allows int as bool)
        self.visit_children(node)

    def visit_WhileStmt(self, node):
        self.visit_children(node)
        
    def visit_ForStmt(self, node):
        # Deploy loop scope handled by Block usually, but 'i' is declared inside ( )
        # So we enter scope BEFORE visiting children
        self.symbol_table.enter_scope()
        self.visit_children(node)
        self.symbol_table.exit_scope()

    # --- Expressions (Returning Types) ---
    def visit_Identifier(self, node):
        var_name = node.value
        
        #  Treat Ally/Enemy as Boolean Literals (flag), not variables
        if var_name in ("Ally", "Enemy"):
            return "flag"

        info = self.symbol_table.lookup(var_name)
        if info:
            if not info['initialized']:
                self.log_warning(f"Variable '{var_name}' used but might not be initialized", node.line)
            return info['type']
        else:
            self.log_error(f"Variable '{var_name}' not declared", node.line)
            return "unknown"
        
    def visit_Number(self, node):
        if "." in node.value:
            return "force" # float
        return "soldier" # int

    def visit_String(self, node):
        return "intel"
    
    def visit_Bool(self, node):
        return "flag"

    def visit_AdditiveExpr(self, node):
        # Left Op Right
        left_type = self.visit(node.children[0])
        right_type = self.visit(node.children[2])
        line = node.line
        
        # Rule: No String + Int
        if (left_type == "intel" and right_type != "intel") or \
           (right_type == "intel" and left_type != "intel"):
             self.log_error("Cannot add String (intel) with Number", line)
             return "error"
             
        # Rule: No Boolean Math
        if left_type == "flag" or right_type == "flag":
            self.log_error("Cannot perform math on Boolean (flag)", line)
            return "error"

        # Rule: String + String = String
        if left_type == "intel" and right_type == "intel":
            return "intel"
            
        # Rule: Float promotion
        if left_type == "force" or right_type == "force":
            return "force"
            
        return "soldier" # default int

    def visit_TermExpr(self, node):
        # Mult/Div
        left_type = self.visit(node.children[0])
        right_type = self.visit(node.children[2])
        
        if left_type == "intel" or right_type == "intel":
            self.log_error("Cannot multiply/divide Strings", node.line)
            return "error"
            
        if left_type == "force" or right_type == "force":
            return "force"
        return "soldier"

    # --- Helpers ---
    def check_assignment_compatibility(self, var_type, expr_type, line):
        if expr_type == "error" or expr_type == "unknown": return

        # Error: Int = Float 
        if var_type == "soldier" and expr_type == "force":
            self.log_error(f"Type Mismatch: Cannot assign 'force' (float) to 'soldier' (int)", line)
        
        # Error: Int = String
        elif var_type == "soldier" and expr_type == "intel":
             self.log_error(f"Type Mismatch: Cannot assign 'intel' (string) to 'soldier' (int)", line)

        # Error: String = Int
        elif var_type == "intel" and expr_type == "soldier":
             self.log_error(f"Type Mismatch: Cannot assign 'soldier' (int) to 'intel' (string)", line)
             