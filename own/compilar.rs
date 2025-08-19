// Rust Online Compiler Server
// Equivalent to compilar.py but implemented in Rust
// 
// Dependencies needed in Cargo.toml:
// [dependencies]
// actix-web = "4.4"
// actix-files = "0.6"
// serde = { version = "1.0", features = ["derive"] }
// serde_json = "1.0"
// tokio = { version = "1.0", features = ["full"] }
// tempfile = "3.8"
// uuid = { version = "1.6", features = ["v4"] }

use actix_files::Files;
use actix_web::{web, App, HttpResponse, HttpServer, Result, middleware::Logger};
use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};
use std::fs;
use std::path::Path;
use tempfile::NamedTempFile;
use uuid::Uuid;

#[derive(Deserialize)]
struct CodeRequest {
    code: String,
    language: String,
}

#[derive(Serialize)]
struct CodeResponse {
    #[serde(skip_serializing_if = "Option::is_none")]
    output: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    execution_time: f64,
}

// HTML template for the web interface with Monaco Editor
const HTML_TEMPLATE: &str = r#"
<!DOCTYPE html>
<html>
<head>
    <title>Online Compiler</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: #1e1e1e;
            color: #fff;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            display: flex;
            flex-direction: column;
            height: calc(100vh - 40px);
        }
        .header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
            padding: 10px;
            background: #252526;
            border-radius: 5px;
        }
        .editor-container {
            flex: 1;
            display: flex;
            min-height: 0;
            position: relative;
        }
        .editor-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #252526;
            border-radius: 5px;
            overflow: hidden;
            min-width: 200px;
        }
        .resizer {
            width: 4px;
            background: #3e3e42;
            cursor: col-resize;
            position: relative;
            margin: 0 5px;
            border-radius: 2px;
            transition: background 0.2s;
        }
        .resizer:hover {
            background: #0e639c;
        }
        .resizer.dragging {
            background: #0e639c;
        }
        .editor-header {
            background: #2d2d30;
            padding: 10px;
            border-bottom: 1px solid #3e3e42;
            font-size: 14px;
            font-weight: bold;
        }
        #editor {
            flex: 1;
            min-height: 400px;
        }
        .output-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #252526;
            border-radius: 5px;
            overflow: hidden;
        }
        .output-header {
            background: #2d2d30;
            padding: 10px;
            border-bottom: 1px solid #3e3e42;
            font-size: 14px;
            font-weight: bold;
        }
        .output { 
            flex: 1;
            background: #1e1e1e; 
            padding: 15px; 
            white-space: pre-wrap;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            overflow-y: auto;
            color: #d4d4d4;
        }
        .output.error {
            color: #f48771;
        }
        button { 
            padding: 10px 20px; 
            background: #0e639c; 
            color: white; 
            border: none; 
            border-radius: 5px;
            cursor: pointer;
            margin: 0 5px;
            transition: background 0.2s;
        }
        button:hover { 
            background: #1177bb; 
        }
        button:disabled {
            background: #666;
            cursor: not-allowed;
        }
        select { 
            padding: 8px 12px; 
            background: #3c3c3c;
            color: #fff;
            border: 1px solid #555;
            border-radius: 3px;
            margin: 0 5px;
        }
        .loading {
            color: #ffd700;
        }
        h1 {
            margin: 0;
            color: #fff;
        }
    </style>
    <script src="/monaco-editor/vs/loader.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Online Compiler</h1>
            <label>Language:</label>
            <select id="language">
                <option value="python">Python</option>
                <option value="cpp">C++</option>
                <option value="c">C</option>
                <option value="java">Java</option>
                <option value="kotlin">Kotlin</option>
                <option value="javascript">JavaScript</option>
                <option value="rust">Rust</option>
                <option value="sql">SQL</option>
                <option value="text">Text</option>
            </select>
            <button onclick="runCode()" id="runBtn">▶ Run Code</button>
            <button onclick="clearOutput()">🗑 Clear Output</button>
        </div>
        
        <div class="editor-container">
            <div class="editor-panel">
                <div class="editor-header">
                    <span id="filename">main.py</span>
                </div>
                <div id="editor"></div>
            </div>
            
            <div class="resizer" id="resizer"></div>
            
            <div class="output-panel">
                <div class="output-header">Output</div>
                <div id="output" class="output">Output will appear here...</div>
            </div>
        </div>
    </div>

    <script>
        let editor;
        
        // Initialize Monaco Editor
        require.config({ paths: { vs: '/monaco-editor/vs' }});
        require(['vs/editor/editor.main'], function () {
            editor = monaco.editor.create(document.getElementById('editor'), {
                value: `# Python example
print("Hello, World!")
for i in range(3):
    print(f"Count: {i}")`,
                language: 'python',
                theme: 'vs-dark',
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                wordWrap: 'on',
                tabSize: 4,
                insertSpaces: true
            });
        });
        
        // Language examples
        const examples = {
            python: {
                code: `# Python example
print("Hello, World!")
for i in range(3):
    print(f"Count: {i}")`,
                filename: 'main.py'
            },
            cpp: {
                code: `// C++ example
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    for(int i = 0; i < 3; i++) {
        cout << "Count: " << i << endl;
    }
    return 0;
}`,
                filename: 'main.cpp'
            },
            c: {
                code: `// C example
#include <stdio.h>

int main() {
    printf("Hello, World!");
    for(int i = 0; i < 3; i++) {
        printf("  ");
        printf("Count: %d", i);
    }
    return 0;
}`,
                filename: 'main.c'
            },
            java: {
                code: `// Java example
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        for(int i = 0; i < 3; i++) {
            System.out.println("Count: " + i);
        }
    }
}`,
                filename: 'Main.java'
            },
            kotlin: {
                code: `// Kotlin example
fun main() {
    println("Hello, World!")
    for (i in 0..2) {
        println("Count: $i")
    }
}`,
                filename: 'Main.kt'
            },
            javascript: {
                code: `// JavaScript example
console.log("Hello, World!");
for(let i = 0; i < 3; i++) {
    console.log(\`Count: \${i}\`);
}`,
                filename: 'main.js'
            },
            rust: {
                code: `// Rust example
fn main() {
    println!("Hello, World!");
    for i in 0..3 {
        println!("Count: {}", i);
    }
}`,
                filename: 'main.rs'
            },
            text: {
                code: `This is a text document.

You can write any text content here:
- Notes
- Documentation
- Plain text
- Lists
- Paragraphs

Feel free to use this for writing and editing text documents!`,
                filename: 'document.txt'
            },
            sql: {
                code: `-- SQL example
-- Create a sample table
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2)
);

-- Insert sample data
INSERT INTO employees VALUES (1, 'John Doe', 'Engineering', 75000.00);
INSERT INTO employees VALUES (2, 'Jane Smith', 'Marketing', 65000.00);
INSERT INTO employees VALUES (3, 'Bob Johnson', 'Engineering', 80000.00);

-- Query the data
SELECT * FROM employees;

-- Group by department and show average salary
SELECT department, AVG(salary) as avg_salary 
FROM employees 
GROUP BY department;

-- Find employees with salary above average
SELECT name, salary 
FROM employees 
WHERE salary > (SELECT AVG(salary) FROM employees);`,
                filename: 'query.sql'
            }
        };
        
        // Handle language change
        document.getElementById('language').addEventListener('change', function() {
            const language = this.value;
            const example = examples[language];
            
            if (editor) {
                // Update editor language and content
                monaco.editor.setModelLanguage(editor.getModel(), language);
                editor.setValue(example.code);
                
                // Update filename
                document.getElementById('filename').textContent = example.filename;
            }
        });
        
        async function runCode() {
            if (!editor) {
                alert('Editor not ready yet. Please wait a moment and try again.');
                return;
            }
            
            const code = editor.getValue();
            const language = document.getElementById('language').value;
            const output = document.getElementById('output');
            const runBtn = document.getElementById('runBtn');
            
            // Update UI for running state
            output.textContent = 'Running...';
            output.className = 'output loading';
            runBtn.disabled = true;
            runBtn.textContent = '⏳ Running...';
            
            try {
                const response = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, language: language })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    const executionTime = result.execution_time ? `\n\n⏱ Execution Time: ${result.execution_time.toFixed(3)} seconds` : '';
                    output.textContent = result.error + executionTime;
                    output.className = 'output error';
                } else {
                    const executionTime = result.execution_time ? `\n\n⏱ Execution Time: ${result.execution_time.toFixed(3)} seconds` : '';
                    output.textContent = (result.output || 'Program executed successfully (no output)') + executionTime;
                    output.className = 'output';
                }
            } catch (error) {
                output.textContent = 'Network Error: ' + error.message;
                output.className = 'output error';
            } finally {
                runBtn.disabled = false;
                runBtn.textContent = '▶ Run Code';
            }
        }
        
        function clearOutput() {
            const output = document.getElementById('output');
            output.textContent = 'Output will appear here...';
            output.className = 'output';
        }
        
        // Add keyboard shortcut for running code (Ctrl+Enter or Cmd+Enter)
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                runCode();
            }
        });
        
        // Draggable resizer functionality
        const resizer = document.getElementById('resizer');
        const editorPanel = document.querySelector('.editor-panel');
        const outputPanel = document.querySelector('.output-panel');
        const container = document.querySelector('.editor-container');
        
        let isResizing = false;
        let startX, startWidth;
        
        resizer.addEventListener('mousedown', function(e) {
            isResizing = true;
            startX = e.clientX;
            startWidth = editorPanel.offsetWidth;
            resizer.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isResizing) return;
            
            const deltaX = e.clientX - startX;
            const newWidth = Math.max(200, Math.min(startWidth + deltaX, container.offsetWidth - 250));
            
            editorPanel.style.width = newWidth + 'px';
            editorPanel.style.flex = 'none';
            
            // Trigger Monaco editor resize
            if (editor) {
                editor.layout();
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isResizing) {
                isResizing = false;
                resizer.classList.remove('dragging');
                document.body.style.cursor = '';
            }
        });
    </script>
</body>
</html>
"#;

// Language runners
impl CodeRunner for PythonRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary file
        let mut temp_file = NamedTempFile::new()?;
        fs::write(temp_file.path(), code)?;
        
        // Execute Python code
        let output = Command::new("python3")
            .arg(temp_file.path())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        if !output.stderr.is_empty() {
            Ok(CodeResponse {
                output: None,
                error: Some(String::from_utf8_lossy(&output.stderr).to_string()),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

trait CodeRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>>;
}

struct PythonRunner;
struct CRunner;
struct CppRunner;
struct JavaRunner;
struct KotlinRunner;
struct JavaScriptRunner;
struct RustRunner;
struct SqlRunner;
struct TextRunner;

impl CodeRunner for CRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary file
        let temp_file = NamedTempFile::with_suffix(".c")?;
        fs::write(temp_file.path(), code)?;
        
        let exe_path = temp_file.path().with_extension("");
        
        // Compile
        let compile_output = Command::new("gcc")
            .args(&[temp_file.path().to_str().unwrap(), "-o", exe_path.to_str().unwrap()])
            .output()?;
        
        if !compile_output.status.success() {
            let execution_time = start_time.elapsed().as_secs_f64();
            return Ok(CodeResponse {
                output: None,
                error: Some(format!("Compilation Error:\n{}", String::from_utf8_lossy(&compile_output.stderr))),
                execution_time,
            });
        }
        
        // Execute
        let run_output = Command::new(&exe_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        // Cleanup
        let _ = fs::remove_file(&exe_path);
        
        if !run_output.stderr.is_empty() {
            Ok(CodeResponse {
                output: None,
                error: Some(String::from_utf8_lossy(&run_output.stderr).to_string()),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&run_output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

impl CodeRunner for CppRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary file
        let temp_file = NamedTempFile::with_suffix(".cpp")?;
        fs::write(temp_file.path(), code)?;
        
        let exe_path = temp_file.path().with_extension("");
        
        // Compile
        let compile_output = Command::new("g++")
            .args(&[temp_file.path().to_str().unwrap(), "-o", exe_path.to_str().unwrap()])
            .output()?;
        
        if !compile_output.status.success() {
            let execution_time = start_time.elapsed().as_secs_f64();
            return Ok(CodeResponse {
                output: None,
                error: Some(format!("Compilation Error:\n{}", String::from_utf8_lossy(&compile_output.stderr))),
                execution_time,
            });
        }
        
        // Execute
        let run_output = Command::new(&exe_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        // Cleanup
        let _ = fs::remove_file(&exe_path);
        
        if !run_output.stderr.is_empty() {
            Ok(CodeResponse {
                output: None,
                error: Some(String::from_utf8_lossy(&run_output.stderr).to_string()),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&run_output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

impl CodeRunner for JavaRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Extract class name from code
        let mut class_name = "Main".to_string();
        for line in code.lines() {
            if line.contains("public class") {
                if let Some(name) = line.split("public class").nth(1) {
                    class_name = name.split('{').next().unwrap_or("Main").trim().to_string();
                    break;
                }
            }
        }
        
        // Create temporary directory and file
        let temp_dir = tempfile::tempdir()?;
        let java_file = temp_dir.path().join(format!("{}.java", class_name));
        fs::write(&java_file, code)?;
        
        // Compile
        let compile_output = Command::new("javac")
            .arg(&java_file)
            .output()?;
        
        if !compile_output.status.success() {
            let execution_time = start_time.elapsed().as_secs_f64();
            return Ok(CodeResponse {
                output: None,
                error: Some(format!("Compilation Error:\n{}", String::from_utf8_lossy(&compile_output.stderr))),
                execution_time,
            });
        }
        
        // Execute
        let run_output = Command::new("java")
            .args(&["-cp", temp_dir.path().to_str().unwrap(), &class_name])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        if !run_output.stderr.is_empty() {
            Ok(CodeResponse {
                output: None,
                error: Some(String::from_utf8_lossy(&run_output.stderr).to_string()),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&run_output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

impl CodeRunner for KotlinRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary file
        let temp_file = NamedTempFile::with_suffix(".kt")?;
        fs::write(temp_file.path(), code)?;
        
        let jar_path = temp_file.path().with_extension("jar");
        
        // Compile
        let compile_output = Command::new("kotlinc")
            .args(&[
                temp_file.path().to_str().unwrap(),
                "-include-runtime",
                "-d",
                jar_path.to_str().unwrap()
            ])
            .output()?;
        
        if !compile_output.status.success() {
            let execution_time = start_time.elapsed().as_secs_f64();
            return Ok(CodeResponse {
                output: None,
                error: Some(format!("Compilation Error:\n{}", String::from_utf8_lossy(&compile_output.stderr))),
                execution_time,
            });
        }
        
        // Execute
        let run_output = Command::new("java")
            .args(&["-jar", jar_path.to_str().unwrap()])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        // Cleanup
        let _ = fs::remove_file(&jar_path);
        
        if !run_output.stderr.is_empty() {
            Ok(CodeResponse {
                output: None,
                error: Some(String::from_utf8_lossy(&run_output.stderr).to_string()),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&run_output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

impl CodeRunner for JavaScriptRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary file
        let temp_file = NamedTempFile::with_suffix(".js")?;
        fs::write(temp_file.path(), code)?;
        
        // Execute
        let output = Command::new("node")
            .arg(temp_file.path())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        if !output.stderr.is_empty() {
            Ok(CodeResponse {
                output: None,
                error: Some(String::from_utf8_lossy(&output.stderr).to_string()),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

impl CodeRunner for RustRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary Cargo project
        let temp_dir = tempfile::tempdir()?;
        let project_dir = temp_dir.path().join("rust_project");
        fs::create_dir_all(&project_dir)?;
        
        // Create Cargo.toml
        let cargo_toml = r#"[package]
name = "rust_project"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "main"
path = "src/main.rs"
"#;
        fs::write(project_dir.join("Cargo.toml"), cargo_toml)?;
        
        // Create src directory and main.rs
        let src_dir = project_dir.join("src");
        fs::create_dir_all(&src_dir)?;
        fs::write(src_dir.join("main.rs"), code)?;
        
        // Compile and run
        let output = Command::new("cargo")
            .args(&["run", "--quiet"])
            .current_dir(&project_dir)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()?;
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        if !output.status.success() {
            Ok(CodeResponse {
                output: None,
                error: Some(format!("Compilation/Runtime Error:\n{}", String::from_utf8_lossy(&output.stderr))),
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(String::from_utf8_lossy(&output.stdout).to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

impl CodeRunner for SqlRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        
        // Create temporary SQLite database
        let temp_db = NamedTempFile::with_suffix(".db")?;
        
        // Split code into statements
        let mut statements = Vec::new();
        let mut current_statement = String::new();
        
        for line in code.lines() {
            let line = line.trim();
            if line.starts_with("--") || line.is_empty() {
                continue;
            }
            current_statement.push_str(line);
            current_statement.push(' ');
            if line.ends_with(';') {
                statements.push(current_statement.trim().to_string());
                current_statement.clear();
            }
        }
        
        if !current_statement.trim().is_empty() {
            statements.push(current_statement.trim().to_string());
        }
        
        let mut results = Vec::new();
        
        for statement in statements {
            if statement.trim().is_empty() {
                continue;
            }
            
            let output = Command::new("sqlite3")
                .args(&[
                    temp_db.path().to_str().unwrap(),
                    &statement
                ])
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .output()?;
            
            if !output.stderr.is_empty() {
                results.push(format!("SQL Error: {}", String::from_utf8_lossy(&output.stderr)));
                break;
            } else {
                let stdout = String::from_utf8_lossy(&output.stdout);
                if statement.trim().to_uppercase().starts_with("SELECT") && !stdout.trim().is_empty() {
                    results.push(format!("Query: {}", statement));
                    results.push("Results:".to_string());
                    results.push(stdout.to_string());
                } else if !stdout.trim().is_empty() {
                    results.push(format!("Statement: {}", statement));
                    results.push(stdout.to_string());
                } else {
                    results.push(format!("Statement: {}", statement));
                    results.push("Statement executed successfully.".to_string());
                }
                results.push("".to_string()); // Empty line for separation
            }
        }
        
        let execution_time = start_time.elapsed().as_secs_f64();
        
        Ok(CodeResponse {
            output: Some(results.join("\n")),
            error: None,
            execution_time,
        })
    }
}

impl CodeRunner for TextRunner {
    fn run(&self, code: &str) -> Result<CodeResponse, Box<dyn std::error::Error>> {
        let start_time = Instant::now();
        let execution_time = start_time.elapsed().as_secs_f64();
        
        if code.trim().is_empty() {
            Ok(CodeResponse {
                output: Some("(Empty text document)".to_string()),
                error: None,
                execution_time,
            })
        } else {
            Ok(CodeResponse {
                output: Some(code.to_string()),
                error: None,
                execution_time,
            })
        }
    }
}

// Route handlers
async fn index() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok()
        .content_type("text/html")
        .body(HTML_TEMPLATE))
}

async fn run_code(req: web::Json<CodeRequest>) -> Result<HttpResponse> {
    let code = &req.code;
    let language = &req.language;
    
    if code.trim().is_empty() {
        return Ok(HttpResponse::BadRequest().json(CodeResponse {
            output: None,
            error: Some("No code provided".to_string()),
            execution_time: 0.0,
        }));
    }
    
    // Basic security check for Python
    if language == "python" {
        let dangerous_imports = ["os", "subprocess", "sys", "eval", "exec", "__import__"];
        if dangerous_imports.iter().any(|&dangerous| code.contains(dangerous)) {
            return Ok(HttpResponse::BadRequest().json(CodeResponse {
                output: None,
                error: Some("Potentially dangerous code detected".to_string()),
                execution_time: 0.0,
            }));
        }
    }
    
    // Execute code based on language
    let result = match language.as_str() {
        "python" => PythonRunner.run(code),
        "c" => CRunner.run(code),
        "cpp" => CppRunner.run(code),
        "java" => JavaRunner.run(code),
        "kotlin" => KotlinRunner.run(code),
        "javascript" => JavaScriptRunner.run(code),
        "rust" => RustRunner.run(code),
        "sql" => SqlRunner.run(code),
        "text" => TextRunner.run(code),
        _ => PythonRunner.run(code), // Default to Python
    };
    
    match result {
        Ok(response) => Ok(HttpResponse::Ok().json(response)),
        Err(e) => Ok(HttpResponse::InternalServerError().json(CodeResponse {
            output: None,
            error: Some(e.to_string()),
            execution_time: 0.0,
        })),
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();
    
    println!("Starting online compiler server with Monaco Editor...");
    println!("Make sure you have the required compilers installed:");
    println!("- Python 3");
    println!("- gcc (for C)");
    println!("- g++ (for C++)");
    println!("- javac and java (for Java)");
    println!("- kotlinc (for Kotlin)");
    println!("- node (for JavaScript)");
    println!("- cargo and rustc (for Rust)");
    println!("- sqlite3 (for SQL)");
    
    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .route("/", web::get().to(index))
            .route("/run", web::post().to(run_code))
            .service(Files::new("/monaco-editor", "./monaco-editor").show_files_listing())
    })
    .bind("0.0.0.0:5003")?
    .run()
    .await
}


// # Navigate to the directory
// cd own/
// # Run the Rust version
// cargo run
// # Access at http://localhost:5003