# ⚔️ WarLang mini Compiler

**WarLang** is a custom, military-themed programming language designed for battlefield simulation logic. It is a statically typed, C-style language that transpiles directly into executable Python code.

## Features

* **Military Syntax:** Use keywords like `soldier` (int), `force` (float), `march` (while), and `shield` (if).
* **Full Pipeline:**
    * **Lexical Analysis:** Regex-based tokenizer.
    * **Syntax Analysis:** Recursive Descent Parser building a Parse tree.
    * **Semantic Analysis:** Type checking, scope management, and logic validation.
    * **Code Generation:** Transpiles WarLang to Python 3.


## 📂 Project Structure

```text
WarLang-Compiler/
├── code_generation.py       # Code Generator (Backend)
├── main.py           # Main Entry Point 
├── parser.py        # Syntax Analyzer
├── scanner.py       # Lexical Analyzer
├── semantic.py      # Semantic Analyzer 
├── WarLang_Ref.txt  # Language Documentation
```
## Installation & Setup

This project is designed to run in a Python **Virtual Environment (venv)** to ensure a clean workspace.

### 1. Clone the Repository
Open your terminal and run:

```bash
git clone [https://github.com/YourUsername/WarLang-Compiler.git](https://github.com/YourUsername/WarLang-Compiler.git)
cd WarLang-Compiler
```
### 2. Set Up the Virtual Environment(Win)
```bash
# 1. Create the virtual environment
python -m venv venv

# 2. Activate the environment
.\venv\bin\activate.ps1
```
### 3. Run the Compiler
Once the environment is active
```bash
python main.py
```
