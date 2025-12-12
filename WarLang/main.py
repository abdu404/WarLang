import tkinter as tk
from tkinter import scrolledtext, messagebox
from scanner import tokenize
from parser import Parser
from semantic import SemanticAnalyzer
from code_generation import CodeGenerator  

class WarLangGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WarLang Mini Compiler IDE")
        self.root.geometry("1000x600")
        
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill=tk.X)
        
        lbl_title = tk.Label(top_frame, text="⚔ WarLang Code Editor ⚔", font=("Arial", 16, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=20)
        
        
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT, padx=20)

        btn_clear = tk.Button(btn_frame, text="CLEAR", bg="#0D32E7", fg="white", 
                              font=("Arial", 9, "bold italic"), width=7, command=self.clear_console)
        btn_clear.pack(side=tk.LEFT, padx=5)

        btn_compile = tk.Button(btn_frame, text="RUN", bg="#0D32E7", fg="white", 
                                font=("Arial", 9, "bold italic"), width=7, command=self.run_compiler)
        btn_compile.pack(side=tk.LEFT, padx=5)  

        paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.LabelFrame(paned_window, text="Source Code (.war)", padx=5, pady=5)
        self.code_input = scrolledtext.ScrolledText(left_frame, width=50, height=30, font=("Consolas", 11))
        self.code_input.pack(fill=tk.BOTH, expand=True)
        # Default text
        self.code_input.insert(tk.END, """battle() {
    intel name = "Captain";
    shout("Hello Sir WarLang!", name);
}""")
        paned_window.add(left_frame)

        right_frame = tk.LabelFrame(paned_window, text="Compiler Output", padx=5, pady=5)
        self.console_output = scrolledtext.ScrolledText(right_frame, width=50, height=30, font=("Consolas", 10), bg="#f0f0f0")
        self.console_output.pack(fill=tk.BOTH, expand=True)
        paned_window.add(right_frame)

    def log(self, text, tag=None):
        self.console_output.insert(tk.END, text + "\n", tag)
        self.console_output.see(tk.END)

    def clear_console(self):
        """Clears the Right Output Panel"""
        self.console_output.delete(1.0, tk.END)

    def run_compiler(self):
        self.clear_console()
        self.log(">>> STARTING COMPILATION...", "info")

        code = self.code_input.get(1.0, tk.END).strip()
        if not code:
            self.log("[!] Error: Source code is empty.")
            return

        try:
            self.log("\n[1] TOKENIZING...")
            tokens = tokenize(code)
            self.log(f"    {len(tokens)} tokens generated.")

            self.log("\n[2] PARSING...")
            parser = Parser(tokens)
            root = parser.parse()

            if parser.errors:
                self.log("\nΧ [PARSING FAILED]", "error")
                for err in parser.errors:
                    self.log(f"    - {err}")
                return # STOP

            self.log("    ✔ Parse Tree built successfully.")

            self.log("\n[3] SEMANTIC ANALYSIS...")
            analyzer = SemanticAnalyzer()
            analyzer.analyze(root)

            if analyzer.warnings:
                self.log("    ⚠️ Warnings Found:", "warning")
                for w in analyzer.warnings: self.log(f"      - {w}")

            if analyzer.errors:
                self.log("\nΧ [SEMANTIC FAILED]", "error")
                for err in analyzer.errors:
                    self.log(f"    - {err}")
                return # STOP

            self.log("    ✔ Semantic checks passed.")

            self.log("\n[4] CODE GENERATION...")
            generator = CodeGenerator()
            python_code = generator.generate(root)
            
            self.log("\n     GENERATED PYTHON CODE")
            self.log("="*40)
            self.log(python_code, "code")
            self.log("="*40)
            
            self.log("\n    ✔ COMPILATION COMPLETE.")

        except Exception as e:
            self.log(f"\n[!] CRITICAL COMPILER CRASH: {e}", "error")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    root = tk.Tk()
    app = WarLangGUI(root)
    app.console_output.tag_config("error", foreground="red")
    app.console_output.tag_config("warning", foreground="orange")
    app.console_output.tag_config("code", foreground="blue", font=("Consolas", 10, "bold"))
    app.console_output.tag_config("info", foreground="green")
    
    root.mainloop()