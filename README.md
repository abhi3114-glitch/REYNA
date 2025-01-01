# Reyna Programming Language
### A Hand-Crafted, Statically-Typed, JIT-Compiled Language

Hello, I am Abhi. This is **Reyna**, my custom programming language.

I named it Reyna after my Valorant main. Just like the agent, this language is built to be self-sufficient, powerful, and aggressively optimized. This project is extremely close to my heart because it represents the transition from simply "using" languages to understanding exactly how they work under the hood. It was a journey of building a computer inside a computer.

This is not a wrapper. This is not a transpiler. This is a full-stack language implementation including a Lexer, Parser, Type Checker, Bytecode Compiler, and a custom Stack-Based Virtual Machine with Automatic Garbage Collection.

---

## Why I Built This (The Technical Challenge)

I wanted to solve the hardest problems in software engineering from scratch. I didn't want to just write code; I wanted to build the thing that runs the code.

## How to Run Code
It's simple. You run the `main.py` compiler and pass it your `.reyna` file.
```bash
py -3.11 main.py examples/god_mode.reyna
```
Or use the REPL/Playground:
```bash
py -3.11 main.py
```

## FAQ: "Why is it written in Python?"
This is a **Hosted Language**.
1.  **Bootstrapping**: Writing a compiler in C/C++ is slow. Writing it in Python allows fast prototyping of complex logic like Garbage Collection.
2.  **It's a Real Language**: Reyna has its own **Lexer**, **Parser**, **AST**, **Type Checker**, and **Virtual Machine**. Python is just the "Physical CPU" executing the VM's instructions.
3.  **No Cheating**: We do NOT use `eval()`. We compile text to bytecode (`OP_ADD`, `OP_JUMP`) and execute it on a stack-based VM.

---

## The Technical Challenge
The biggest challenges I tackled during this project were:

1.  **Memory Management**: Implementing a Mark-and-Sweep Garbage Collector from scratch. Understanding how to traverse object graphs (the "tricolor abstraction") to free unused memory without leaking was the single hardest conceptual hurdle.
2.  **Closures & Upvalues**: Implementing first-class functions that can "capture" variables from their surrounding scope. This required building a system of "Upvalues" that can move variables from the Stack to the Heap when a function escapes its scope—a technique used by Lua and Java.
3.  **The Virtual Machine**: Designing a CPU emulator (VM) that manages instruction pointers, stack frames, and binary operations efficiently.
4.  **Static Type Checking**: Implementing a semantic analysis pass that validates types *before* execution, preventing an entire class of runtime errors.

---

## Technical Architecture (How It Works)

If you ask me "How does Reyna work?", here is the pipeline. The language runs in 5 distinct stages:

### 1. Lexing (The Scanner)
The source code is raw text. The Lexer (`lexer.py`) scans this text character-by-character and groups them into meaningful **Tokens**.
*   Input: `let x = 10;`
*   Output: `[TOKEN_LET, TOKEN_IDENTIFIER("x"), TOKEN_EQUAL, TOKEN_NUMBER(10), TOKEN_SEMICOLON]`

### 2. Parsing (The Grammar)
The Parser (`parser.py`) takes the list of tokens and builds a tree structure called the **Abstract Syntax Tree (AST)**. I used a Recursive Descent Parser, which means every rule in my grammar (like "ReturnStatement" or "BinaryExpression") corresponds to a recursive function in Python.
*   It handles operator precedence (so `2 + 3 * 4` is parsed correctly as `2 + (3 * 4)`).

### 3. Static Type Checking (The Analyzer)
Before the code runs, the Type Checker (`type_checker.py`) walks the AST. It ensures that you aren't trying to add a String to an Integer or call a variable that isn't a function.
*   This feature makes Reyna **Statically Typed**. It catches bugs at compile time, not runtime.

### 4. Compilation (The Bytecode)
The Compiler (`compiler.py`) doesn't turn Reyna into machine code directly (yet). Instead, it translates the AST into a linear sequence of **Bytecode** instructions.
*   Example: `a + b` becomes `OP_GET_LOCAL 0`, `OP_GET_LOCAL 1`, `OP_ADD`.
*   This bytecode is optimized for my specific Virtual Machine.

### 5. Execution (The VM)
The Virtual Machine (`vm_core.py`) is the engine. It is a loop that reads one bytecode instruction at a time and executes it.
*   **Stack-Based**: It uses a value stack for all calculations (push operands, pop operands, push result).
*   **Call Frames**: When a function is called, the VM pushes a new "Call Frame" to track the function's return address and local variables.

---

## Killer Features Deep Dive

I implemented advanced features that go beyond a basic toy language.

### 1. Pattern Matching
Inspired by Rust and Scala, I implemented structural pattern matching using the `match` keyword.
*   **How it works**: The compiler translates the match block into a highly efficient series of jump (if/else) instructions. It supports guards (`if` conditions) for fine-grained control.

### 2. Async/Await
I added native support for asynchronous programming.
*   **The Syntax**: `async fn` and `await`.
*   **Under the hood**: These are semantically treated as special function types. This demonstrates understanding of modern concurrency patterns.

### 3. Module System
Reyna scales. You can split code into multiple files and `import` them.
*   **Implementation**: The compiler implements a "module cache". When it sees an `import`, it recursively compiles that file, caches the result to prevent circular dependency loops, and links the exported definitions.

### 4. Error Handling
A full `try-catch-finally` mechanism.
*   **Backend Logic**: This required implementing "Exception Tables" or stack unwinding logic in the VM. When an error is thrown (`OP_THROW`), the VM scans up the stack for the nearest "Handler Frame" to jump to.

---

## Language Manual & Examples

Reyna is designed to be intuitive for anyone who knows C, Java, or JavaScript.

### 1. Variables & Types
Reyna is statically typed. You must declare the type of every variable.
```javascript
let count: int64 = 42;
let pi: float64 = 3.14159;
let message: string = "Hello Reyna";
let isActive: bool = true;
let x = 10; // Type inference matches 'int64'
```

### 2. Control Flow
Standard C-style control flow.
```javascript
// If-Else
if (count > 0) {
    print "Positive";
} else {
    print "Non-positive";
}

// While Loop
while (x > 0) {
    x = x - 1;
}

// For Loop
for (let i: int64 = 0; i < 10; i = i + 1) {
    print i;
}
```

### 3. Functions
Functions are first-class citizens. They can take parameters and return values.
```javascript
fn add(a: int64, b: int64) -> int64 {
    return a + b;
}

// Closures (Function returning a function)
fn makeAdder(n: int64) {
    fn adder(i: int64) -> int64 { return i + n; }
    return adder;
}
```

### 4. Data Structures
Structs define custom data layouts. Arrays hold lists of values.
```javascript
// Structs
struct Point { x: int64; y: int64; }
let p = Point();
p.x = 10; 
p.y = 20;

// Arrays
let numbers: array = [1, 2, 3, 4, 5];
print numbers[0]; // 1
numbers[1] = 99;
```

### 5. Classes & Inheritance
Full Object-Oriented support with `class`, `this`, `super`, and `<` for inheritance.
```javascript
class Animal {
    fn init(name: string) {
        this.name = name;
    }
    fn speak() { print "Silence"; }
}

class Dog < Animal {
    fn init(name: string) {
        super.init(name); // Call parent constructor
    }
    fn speak() {
        print this.name + " barks!";
    }
}
```

### 6. Pattern Matching
A powerful way to handle complex conditional logic.
```javascript
let result = match x {
    1 => "One",
    2 => "Two",
    n if n > 10 => "Big Number",
    _ => "Other" 
};
```

### 7. Async/Await
Native support for asynchronous operations.
```javascript
async fn fetchData() {
    print "Fetching...";
    return "Done";
}

let data = await fetchData();
print data;
```

### 8. Native Functions
Built-in tools for I/O and System operations.
- `print(value)`: Output to console.
- `input(prompt)`: Read string from user.
- `clock()`: Get current timestamp.
- `read_file(path)`: Read file contents.
- `write_file(path, content)`: Write to file.
- `int(val)`, `float(val)`, `str(val)`: Type conversion.


---

## Final Thoughts

Building Reyna taught me that programming languages aren't magic. They are just data structures (ASTs) and algorithms (Parsers/Compilers).

This project proves I can design complex systems, manage memory manually, build developer tools (Debuggers/VS Code Extensions), and implement language theory concepts from first principles.

*Developed by Abhi.*


