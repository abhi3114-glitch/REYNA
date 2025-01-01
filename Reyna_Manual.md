# Reyna Language Manual 1.0

This document is the official reference for writing code in the Reyna Programming Language.

## 1. Getting Started

### Running Code
To execute a Reyna script (`.reyna`), use the compiler CLI:
```bash
py main.py path/to/script.reyna
```

---

## 2. Primitive Types

Reyna is statically typed. Variables must have a specific type.

| Type | Keyword | Example |
| :--- | :--- | :--- |
| Integer (64-bit) | `int64` | `10`, `-5`, `0` |
| Float (64-bit) | `float64` | `3.14`, `-0.01` |
| Boolean | `bool` | `true`, `false` |
| String | `string` | `"Hello World"` |
| Array | `array` | `[1, 2, "three"]` |
| Function | `fn` | `fn(x: int64)` |
| Void | `void` | `return;` |

---

## 3. Variables

Use the `let` keyword. Types are required (though inference works for direct assignments).

```javascript
let x: int64 = 10;
let name: string = "Reyna";
let pi: float64 = 3.14159;

// Reassignment
x = 20; 
```

---

## 4. Control Flow

### If / Else
```javascript
if (x > 10) {
    print "Greater";
} else if (x == 10) {
    print "Equal";
} else {
    print "Lesser";
}
```

### While Loop
```javascript
let i: int64 = 0;
while (i < 5) {
    print i;
    i = i + 1;
}
```

### For Loop
Standard C-style loop syntax:
```javascript
// init; condition; increment
for (let j: int64 = 0; j < 10; j = j + 1) {
    print j;
}
```

---

## 5. Functions

Defined with `fn`. Use types for parameters and return values.

```javascript
// Basic function
fn add(a: int64, b: int64) -> int64 {
    return a + b;
}

// Void return type (optional)
fn sayHello(name: string) {
    print "Hello " + name;
}
```

### Closures
Functions can be defined inside other functions and return them.
```javascript
fn makeMultiplier(factor: int64) {
    fn multiply(start: int64) -> int64 {
        return start * factor;
    }
    return multiply;
}
let doubler = makeMultiplier(2);
print doubler(10); // 20
```

---

## 6. Data Structures

### Structs
Simple data containers.
```javascript
struct Config {
    port: int64;
    host: string;
}

let c = Config();
c.port = 8080;
c.host = "localhost";
```

### Arrays
Dynamic lists.
```javascript
let list: array = ["a", "b", "c"];
print list[0]; // "a"
list[1] = "z";
```

---

## 7. Classes (OOP)

Reyna supports single inheritance classes.

```javascript
class Parent {
    fn init() {
        this.baseValue = 100;
    }
    fn show() { print this.baseValue; }
}

class Child < Parent {
    fn init() {
        super.init(); // Initialize parent
        this.childValue = 50;
    }
    fn show() {
        super.show();
        print this.childValue;
    }
}
```

---

## 8. Pattern Matching

Use `match` for advanced control flow.

```javascript
let val = 15;
let desc = match val {
    0 => "Zero",
    10 => "Ten",
    n if n > 10 => "Greater than Ten",
    _ => "Unknown"
};
```

---

## 9. Asynchronous Programming

Use `async` and `await`.

```javascript
async fn loadData() {
    print "Loading...";
    return 42;
}

let result = await loadData();
```

---

## 10. Standard Library

These functions are built-in and available everywhere.

| Function | Usage | Description |
| :--- | :--- | :--- |
| `print(val)` | `print "Hi"` | Prints value to stdout with newline. |
| `input(msg)` | `let s = input("Name?")` | Reads a line of text from stdin. |
| `clock()` | `let t = clock()` | Returns current time in seconds (float). |
| `int(val)` | `int("123")` | Converts value to Integer. |
| `float(val)` | `float("3.5")` | Converts value to Float. |
| `str(val)` | `str(100)` | Converts value to String. |
| `read_file(p)` | `read_file("data.txt")` | Returns file content as string. |
| `write_file(p, c)` | `write_file("log.txt", "HI")` | Writes string to file. |
| `python(code)` | `python("import os; os.system('cls')")` | **God Mode**: Execute arbitrary Python code. |

---

*Reyna Programming Language Reference Manual*







