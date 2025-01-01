# Reyna VS Code Extension

Syntax highlighting and code snippets for the Reyna programming language.

## Features

- **Syntax Highlighting**: Full support for Reyna keywords, types, classes, and operators
- **Code Snippets**: Quick templates for functions, classes, loops, and more
- **Bracket Matching**: Auto-closing and matching for `{}`, `[]`, `()`
- **Comment Support**: Line (`//`) and block (`/* */`) comments

## Installation

### From VSIX (Local)

1. Package the extension:
   ```bash
   cd reyna-vscode
   npx vsce package
   ```

2. Install in VS Code:
   - Press `Ctrl+Shift+P`
   - Type "Install from VSIX"
   - Select the generated `.vsix` file

### From Source (Development)

1. Copy this folder to `~/.vscode/extensions/reyna-language`
2. Reload VS Code

## Snippets

| Prefix | Description |
|--------|-------------|
| `fn` | Function declaration |
| `class` | Class with init |
| `classext` | Class with inheritance |
| `struct` | Struct definition |
| `for` | For loop |
| `while` | While loop |
| `if` | If statement |
| `ifelse` | If-else statement |
| `let` | Variable declaration |
| `print` | Print statement |
| `closure` | Closure pattern |
| `try` | Try-catch block |
| `async` | Async function |

## Contributing

This extension is part of the [Reyna Language](https://github.com/abhi3114-glitch/reyna) project.






