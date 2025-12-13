class CodeGenerator:
    def __init__(self):
        # We need to track indentation because Python crashes if spacing is wrong.
        # 0 = No indent, 1 = 4 spaces, 2 = 8 spaces, etc.
        self.indent_level = 0
        
        # This list will hold all the lines of Python code we generate.
        # At the end, we stick them all together.
        self.output = []

    # --- The Main Start Button ---
    def generate(self, node):
        self.output = []      # Clear any old code
        self.indent_level = 0 # Reset indentation
        
        # Start walking the tree from the top (Root)
        self.visit(node)
        
        # Join all the lines into one big string and return it
        return "".join(self.output)

    # --- Helper: Makes the Spaces ---
    def indent(self):
        # Adds 4 spaces for every level of indentation.
        # Level 1 = "    ", Level 2 = "        "
        return "    " * self.indent_level

    # --- Helper: Writes Code ---
    def emit(self, code, newline=False):
        # Adds a piece of code to our list.
        self.output.append(code)
        if newline:
            self.output.append("\n")

    # --- Helper: Writes a Full Line ---
    def emit_line(self, code):
        # This adds the indentation + the code + a "Enter" (newline)
        self.output.append(self.indent() + code + "\n")

    # --- The Brain (Visitor Pattern) ---
    def visit(self, node):
        # This function looks at the node name (e.g., "IfStmt")
        # and tries to find a function named "visit_IfStmt".
        # If it finds it, it runs it. If not, it just visits the children.
        method_name = f'visit_{node.name}'
        visitor = getattr(self, method_name, self.visit_children)
        return visitor(node)

    def visit_children(self, node):
        # Just goes through all the kids of the current node
        for child in node.children:
            self.visit(child)

    #=====TRANSLATION RULES START=====

    # --- Program Structure ---
    def visit_Program(self, node):
        self.visit_children(node)

    def visit_ImportList(self, node):
        # Process all imports (#call ...)
        for child in node.children:
            self.visit(child)
        # Add an empty line after imports to look nice
        self.emit("\n", newline=False) 

    def visit_IncludeStmt(self, node):
        # Translate: #call lib  ->  import lib
        lib_name = node.children[0].value
        self.emit_line(f"import {lib_name}")

    def visit_GlobalDeclarations(self, node):
        self.visit_children(node)
        self.emit("\n", newline=False)

    def visit_MainFunction(self, node):
        # Translate: battle()  ->  if __name__ == "__main__":
        self.emit_line('if __name__ == "__main__":')
        
        # Everything inside main must be indented
        self.visit_children(node)

    def visit_Block(self, node):
        # When we enter a { block }, we must indent Python code.
        self.indent_level += 1
        self.visit_children(node)
        # When we leave a } block, we go back.
        self.indent_level -= 1

    def visit_StatementList(self, node):
        self.visit_children(node)

    # --- Variables ---
    def visit_Declaration(self, node):
        # Translate: soldier x = 10;  ->  x = 10
        # We don't need the type (soldier) in Python.
        var_name = node.children[1].value
        
        if len(node.children) > 2:
            # If it has a value (= 10), we need to translate the math part (10)
            expr_code = self.visit_expression(node.children[3])
            self.emit_line(f"{var_name} = {expr_code}")
        else:
            # If declared but empty (soldier x;), set it to None in Python
            self.emit_line(f"{var_name} = None")

    def visit_Assignment(self, node):
        # Translate: x = y + 1;  ->  x = y + 1
        var_name = node.children[0].value
        expr_code = self.visit_expression(node.children[2])
        self.emit_line(f"{var_name} = {expr_code}")

    # --- Control Flow (If / Loop) ---
    def visit_IfStmt(self, node):
        # Translate: shield (x > 0) -> if x > 0:
        
        # 1. Get the condition string (e.g., "x > 0")
        condition = self.visit_expression(node.children[0])
        self.emit_line(f"if {condition}:")
        
        # 2. Visit the code inside the IF block
        self.visit(node.children[1])
        
        # 3. Check if there is an ELSE (retreat)
        if len(node.children) > 2:
            self.emit_line("else:")
            self.visit(node.children[2])

    def visit_ElsePart(self, node):
        self.visit_children(node)

    def visit_WhileStmt(self, node):
        # Translate: march (x > 0) -> while x > 0:
        condition = self.visit_expression(node.children[0])
        self.emit_line(f"while {condition}:")
        self.visit(node.children[1])

    def visit_ForStmt(self, node):
        # Translate: deploy(i=0; i<5; i++) 
        # Python doesn't have C-style loops, so we fake it with a WHILE loop.
        
        # 1. Write the Init: "i = 0"
        self.visit(node.children[0])
        
        # 2. Write the While Condition: "while i < 5:"
        condition = self.visit_expression(node.children[1])
        self.emit_line(f"while {condition}:")
        
        # 3. Increase indent for the loop body
        self.indent_level += 1
        
        # 4. Write the loop body (the user's code)
        # Note: The 'Block' node usually indents, but since we are manually building
        # a while loop, we grab the statements directly to avoid double indenting.
        block_node = node.children[3]
        statement_list = block_node.children[0]
        self.visit(statement_list)
        
        # 5. Write the Update step at the bottom: "i += 1"
        update_node = node.children[2]
        
        if update_node.name == "Assignment":
            # Case: i = i + 1
            var = update_node.children[0].value
            expr = self.visit_expression(update_node.children[2])
            self.emit_line(f"{var} = {expr}")
            
        elif update_node.name == "Increment":
            # Case: i++
            var = update_node.value.replace("++", "") # Remove '++'
            self.emit_line(f"{var} += 1") # Use Python syntax
            
        # 6. Decrease indent (Exit loop)
        self.indent_level -= 1

    # --- Input / Output ---
    def visit_OutputStmt(self, node):
        # Translate: shout("Hi", x) -> print("Hi", x)
        args = []
        for child in node.children:
            # Turn every argument into a string
            args.append(self.visit_expression(child))
        
        # Join them with commas
        args_str = ", ".join(args)
        self.emit_line(f"print({args_str})")

    def visit_InputStmt(self, node):
        # Translate: scout(x) -> x = input()
        var_name = node.children[0].value
        self.emit_line(f"{var_name} = input()")

    # --- Math & Logic (Returning Strings) ---
    # These functions DO NOT write lines. They return text chunks (like "5 + 5")
    # so other functions can use them.
    
    def visit_expression(self, node):
        # If it's math (Left + Right)
        if node.name in ("RelationalExpr", "AdditiveExpr", "TermExpr"):
            left = self.visit_expression(node.children[0])
            op = node.children[1].value
            right = self.visit_expression(node.children[2])
            return f"({left} {op} {right})"
        
        # If it's a number
        elif node.name == "Number":
            return node.value
        
        # If it's a string
        elif node.name == "String":
            return node.value 
        
        # If it's a variable or boolean keyword
        elif node.name == "Identifier":
            name = node.value
            # Translate WarLang Booleans to Python Booleans
            if name == "Ally": return "True"
            if name == "Enemy": return "False"
            return name
            
        elif node.name == "Bool":
            return "True" if node.value == "Ally" else "False"
            
        return ""