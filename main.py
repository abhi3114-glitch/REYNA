import sys
import os
import argparse

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from lexer import Lexer
from parser import Parser
from compiler import Compiler
from compiler import Compiler
from vm_core import VM

def run_file(path, mode, check_only=False):
    with open(path, "r") as f:
        source = f.read()
    run(source, mode, check_only)

def run(source, mode, check_only=False):
    # Phase 1: Lexing
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    
    # Phase 2: Parsing
    parser = Parser(tokens)
    statements = parser.parse()
    # print(f"Debug: Parsed {len(statements)} statements")
    
    if not statements:
        # print("Error: No statements parsed.")
        return

    # Phase 2.5: Type Checking
    from type_checker import TypeChecker
    checker = TypeChecker()
    if not checker.check(statements):
        print("Type checking failed. Aborting.")
        return

    # Phase 3: Compilation
    compiler = Compiler()
    chunk = compiler.compile(statements)
    # print("Debug: Compiled chunk")

    # Phase 4: Execution
    if mode == "vm":
        # Debug Disassembly
        # chunk.disassemble("Script")
        vm = VM()
        try:
            vm.interpret(chunk)
        except Exception:
            import traceback
            import sys
            print(traceback.format_exc())
            sys.stdout.flush()
    elif mode == "jit":
        from jit import ReynaJIT
        jit = ReynaJIT()
        jit.compile_and_run(statements)

def main():
    parser = argparse.ArgumentParser(description="Reyna Programming Language")
    parser.add_argument("file", nargs="?", help="Source file to run")
    parser.add_argument("--mode", choices=["vm", "jit"], default="vm", help="Execution mode")
    parser.add_argument("--check", action="store_true", help="Type check only")
    
    args = parser.parse_args()
    
    if args.file:
        run_file(args.file, args.mode, args.check)
    else:
        # REPL (check ignored)
        print("Reyna v0.2 (Typed)")
        while True:
            try:
                line = input("> ")
                if line == "exit": break
                run(line, args.mode)
            except EOFError:
                break
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main()




