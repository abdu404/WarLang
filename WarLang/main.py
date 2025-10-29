from scanner import tokenize
import os

def main():
    
    base_dir = os.path.dirname(__file__)
    source_path = os.path.join(base_dir, "..", "examples", "test.war")

    #Read source code
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find source file at {source_path}")
        return

    # Tokenize 
    tokens = tokenize(code)

    #Print tokens 
    print("\n===== TOKENS =====\n")
    for token in tokens:
        print(f"Type: {token.type:<20}  Value: {token.value:<10}  Line: {token.line:<3}  Column: {token.column}")
    print("\n===== END OF TOKENS =====\n")


if __name__ == "__main__":
    main()
