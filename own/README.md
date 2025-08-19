# Online Compiler - Rust Implementation

This is a Rust implementation of the online compiler web application, originally written in Python Flask. It provides a web-based IDE with Monaco Editor for running code in multiple programming languages.

## Features

- **Monaco Editor Integration**: Professional code editor with syntax highlighting
- **Multiple Language Support**:
  - Python
  - C/C++
  - Java
  - Kotlin
  - JavaScript (Node.js)
  - Rust
  - SQL (SQLite)
  - Text files
- **Real-time Execution**: Run code and see results instantly
- **Execution Timing**: Shows execution time for performance analysis
- **Resizable Panels**: Adjustable editor and output panes
- **Security Features**: Basic validation to prevent dangerous code execution

## Prerequisites

Before running the application, ensure you have the following compilers and tools installed:

### Required Tools
- **Rust** (for running this application)
- **Python 3** - for Python code execution
- **GCC** - for C code compilation (`brew install gcc`)
- **G++** - for C++ code compilation (usually comes with gcc)
- **Java JDK** - for Java compilation and execution
- **Kotlin** - for Kotlin compilation (`brew install kotlin`)
- **Node.js** - for JavaScript execution (`brew install node`)
- **Cargo/Rustc** - for Rust code compilation (comes with Rust installation)
- **SQLite3** - for SQL execution (usually pre-installed on macOS)

### Install Dependencies on macOS
```bash
# Install using Homebrew
brew install gcc
brew install kotlin
brew install node
brew install openjdk  # For Java
```

## Installation and Running

1. **Clone or navigate to the project directory**
   ```bash
   cd /path/to/your/project/own/
   ```

2. **Build and run the Rust application**
   ```bash
   cargo run
   ```
   
   Or compile and run separately:
   ```bash
   cargo build --release
   ./target/release/compilar
   ```

3. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5003`

## Usage

1. **Select Language**: Choose your programming language from the dropdown
2. **Write Code**: Use the Monaco Editor to write your code
3. **Run Code**: Click the "▶ Run Code" button or press `Ctrl+Enter` (or `Cmd+Enter` on Mac)
4. **View Output**: See the execution results in the output panel
5. **Adjust Layout**: Drag the resizer to adjust panel sizes

## Project Structure

```
own/
├── compilar.rs          # Main Rust application
├── compilar.py          # Original Python version  
├── Cargo.toml          # Rust dependencies
├── README.md           # This file
└── monaco-editor/      # Monaco Editor assets (required)
```

## Code Execution Flow

1. User submits code through the web interface
2. Server creates temporary files for the code
3. Appropriate compiler/interpreter is invoked
4. Results are captured and returned as JSON
5. Temporary files are cleaned up
6. Results displayed in the web interface

## Security Features

- **Input Validation**: Basic checks for dangerous imports (Python)
- **Timeouts**: Process execution timeouts to prevent infinite loops
- **Temporary Files**: All code execution happens in temporary files
- **Sandboxing**: Limited to available system compilers and interpreters

## API Endpoints

- `GET /` - Main web interface
- `POST /run` - Execute code (JSON API)
- `GET /monaco-editor/*` - Static Monaco Editor assets

### API Request Format
```json
{
    "code": "print('Hello, World!')",
    "language": "python"
}
```

### API Response Format
```json
{
    "output": "Hello, World!\n",
    "execution_time": 0.123
}
```

Or for errors:
```json
{
    "error": "Compilation Error: ...",
    "execution_time": 0.045
}
```

## Differences from Python Version

The Rust implementation provides the same functionality as the original Python Flask version with these improvements:

- **Performance**: Faster startup and request handling
- **Memory Safety**: Rust's ownership system prevents memory-related bugs
- **Concurrent Handling**: Better handling of multiple simultaneous requests
- **Type Safety**: Compile-time guarantees for request/response handling

## Troubleshooting

### Common Issues

1. **Monaco Editor not loading**: Ensure the `monaco-editor` directory is present in the same directory as the executable

2. **Compiler not found**: Install the required compilers for the languages you want to use

3. **Permission errors**: Ensure the application has permission to create temporary files

4. **Port already in use**: The application runs on port 5003 by default. Make sure this port is available.

### Logs
The application uses `env_logger` for logging. Set the `RUST_LOG` environment variable for more detailed logs:
```bash
RUST_LOG=debug cargo run
```

## Contributing

This is a conversion of the original Python Flask application to Rust. Both versions should maintain feature parity.

## License

This project maintains the same license as the original implementation.
