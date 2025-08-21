# Requirements:
# pip install fastapi uvicorn python-multipart

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import tempfile
import os
import signal
import time
import asyncio
from threading import Timer
from typing import Dict, Any

app = FastAPI(
    title="Online Compiler API",
    description="A web-based code compiler supporting multiple languages",
    version="2.0.0"
)

# Pydantic models for request/response
class CodeRequest(BaseModel):
    code: str
    language: str

class CodeResponse(BaseModel):
    output: str = None
    error: str = None
    execution_time: float

# HTML template for the web interface with Monaco Editor
HTML_TEMPLATE = '''
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
        .api-link {
            margin-left: auto;
            color: #0e639c;
            text-decoration: none;
            padding: 8px 15px;
            border: 1px solid #0e639c;
            border-radius: 3px;
            transition: all 0.2s;
        }
        .api-link:hover {
            background: #0e639c;
            color: white;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs/loader.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Online Compiler (FastAPI)</h1>
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
            <a href="/docs" target="_blank" class="api-link">📚 API Docs</a>
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
        require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs' }});
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
        printf(" Count: ", i);
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
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, language: language })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    const executionTime = result.execution_time ? `\\n\\n⏱ Execution Time: ${result.execution_time.toFixed(3)} seconds` : '';
                    output.textContent = result.error + executionTime;
                    output.className = 'output error';
                } else {
                    const executionTime = result.execution_time ? `\\n\\n⏱ Execution Time: ${result.execution_time.toFixed(3)} seconds` : '';
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
'''

def timeout_handler(process):
    """Kill process if it takes too long"""
    try:
        process.kill()
    except:
        pass

async def run_python_code(code: str) -> Dict[str, Any]:
    """Execute Python code safely"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        start_time = time.time()
        
        process = await asyncio.create_subprocess_exec(
            'python3', temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            execution_time = time.time() - start_time
            
            os.unlink(temp_file)
            
            if stderr:
                return {'error': stderr.decode(), 'execution_time': execution_time}
            return {'output': stdout.decode(), 'execution_time': execution_time}
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            os.unlink(temp_file)
            return {'error': 'Code execution timed out', 'execution_time': 5.0}
            
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

async def run_c_code(code: str) -> Dict[str, Any]:
    """Compile and execute C code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            c_file = f.name
        
        exe_file = c_file.replace('.c', '')
        
        # Compile
        compile_process = await asyncio.create_subprocess_exec(
            'gcc', c_file, '-o', exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(compile_process.communicate(), timeout=10)
        
        if compile_process.returncode != 0:
            os.unlink(c_file)
            return {'error': f'Compilation Error:\n{stderr.decode()}', 'execution_time': 0.0}
        
        # Execute
        start_time = time.time()
        run_process = await asyncio.create_subprocess_exec(
            exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(run_process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        
        # Cleanup
        os.unlink(c_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if stderr:
            return {'error': stderr.decode(), 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

async def run_cpp_code(code: str) -> Dict[str, Any]:
    """Compile and execute C++ code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(code)
            cpp_file = f.name
        
        exe_file = cpp_file.replace('.cpp', '')
        
        # Compile
        compile_process = await asyncio.create_subprocess_exec(
            'g++', cpp_file, '-o', exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(compile_process.communicate(), timeout=10)
        
        if compile_process.returncode != 0:
            os.unlink(cpp_file)
            return {'error': f'Compilation Error:\n{stderr.decode()}', 'execution_time': 0.0}
        
        # Execute
        start_time = time.time()
        run_process = await asyncio.create_subprocess_exec(
            exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(run_process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        
        # Cleanup
        os.unlink(cpp_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if stderr:
            return {'error': stderr.decode(), 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

async def run_java_code(code: str) -> Dict[str, Any]:
    """Compile and execute Java code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            java_file = f.name
        
        # Extract class name from code
        class_name = 'Main'  # Default
        for line in code.split('\n'):
            if 'public class' in line:
                class_name = line.split('public class')[1].split('{')[0].strip()
                break
        
        # Rename file to match class name
        correct_file = java_file.replace('.java', f'/{class_name}.java')
        os.makedirs(os.path.dirname(correct_file), exist_ok=True)
        os.rename(java_file, correct_file)
        
        # Compile
        compile_process = await asyncio.create_subprocess_exec(
            'javac', correct_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(compile_process.communicate(), timeout=10)
        
        if compile_process.returncode != 0:
            os.unlink(correct_file)
            return {'error': f'Compilation Error:\n{stderr.decode()}', 'execution_time': 0.0}
        
        # Execute
        class_dir = os.path.dirname(correct_file)
        start_time = time.time()
        run_process = await asyncio.create_subprocess_exec(
            'java', '-cp', class_dir, class_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(run_process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        
        # Cleanup
        os.unlink(correct_file)
        class_file = correct_file.replace('.java', '.class')
        if os.path.exists(class_file):
            os.unlink(class_file)
        
        if stderr:
            return {'error': stderr.decode(), 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

async def run_kotlin_code(code: str) -> Dict[str, Any]:
    """Compile and execute Kotlin code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kt', delete=False) as f:
            f.write(code)
            kt_file = f.name
        
        # Compile
        compile_process = await asyncio.create_subprocess_exec(
            'kotlinc', kt_file, '-include-runtime', '-d', 'output.jar',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(compile_process.communicate(), timeout=15)
        
        if compile_process.returncode != 0:
            os.unlink(kt_file)
            return {'error': f'Compilation Error:\n{stderr.decode()}', 'execution_time': 0.0}
        
        # Execute
        start_time = time.time()
        run_process = await asyncio.create_subprocess_exec(
            'java', '-jar', 'output.jar',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(run_process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        
        # Cleanup
        os.unlink(kt_file)
        if os.path.exists('output.jar'):
            os.unlink('output.jar')
        
        if stderr:
            return {'error': stderr.decode(), 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

async def run_javascript_code(code: str) -> Dict[str, Any]:
    """Execute JavaScript code using Node.js"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            js_file = f.name
        
        start_time = time.time()
        process = await asyncio.create_subprocess_exec(
            'node', js_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        
        os.unlink(js_file)
        
        if stderr:
            return {'error': stderr.decode(), 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

async def run_rust_code(code: str) -> Dict[str, Any]:
    """Compile and execute Rust code"""
    try:
        import shutil
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            rs_file = f.name
        
        temp_dir = tempfile.mkdtemp()
        project_name = 'rust_project'
        project_dir = os.path.join(temp_dir, project_name)
        os.makedirs(project_dir)
        
        # Create Cargo.toml
        cargo_toml = f'''[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "main"
path = "src/main.rs"
'''
        
        with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
            f.write(cargo_toml)
        
        # Create src directory and move the Rust file
        src_dir = os.path.join(project_dir, 'src')
        os.makedirs(src_dir)
        shutil.move(rs_file, os.path.join(src_dir, 'main.rs'))
        
        # Compile and run
        start_time = time.time()
        process = await asyncio.create_subprocess_exec(
            'cargo', 'run', '--quiet',
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
        execution_time = time.time() - start_time
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        if process.returncode != 0:
            return {'error': f'Compilation/Runtime Error:\n{stderr.decode()}', 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

def run_sql_code(code: str) -> Dict[str, Any]:
    """Execute SQL code using SQLite"""
    try:
        import sqlite3
        
        # Create a temporary SQLite database
        db_path = tempfile.mktemp(suffix='.db')
        
        # Split the code into individual statements
        statements = []
        current_statement = ""
        
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('--'):  # Skip comments
                continue
            if line:  # Non-empty line
                current_statement += line + " "
                if line.endswith(';'):  # End of statement
                    statements.append(current_statement.strip())
                    current_statement = ""
        
        # Add any remaining statement without semicolon
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        start_time = time.time()
        
        results = []
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            for statement in statements:
                if not statement.strip():
                    continue
                    
                # Execute the statement
                cursor.execute(statement)
                
                # If it's a SELECT statement, fetch results
                if statement.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    if rows:
                        # Get column names
                        columns = [description[0] for description in cursor.description]
                        results.append(f"Query: {statement}")
                        results.append("Results:")
                        results.append(" | ".join(columns))
                        results.append("-" * (len(" | ".join(columns))))
                        for row in rows:
                            results.append(" | ".join(str(cell) for cell in row))
                        results.append("")  # Empty line for separation
                    else:
                        results.append(f"Query: {statement}")
                        results.append("No results returned.")
                        results.append("")
                else:
                    # For non-SELECT statements, show affected rows
                    results.append(f"Statement: {statement}")
                    results.append(f"Rows affected: {cursor.rowcount}")
                    results.append("")
                    
        except sqlite3.Error as e:
            results.append(f"SQL Error: {str(e)}")
        finally:
            conn.close()
            # Clean up the temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
        
        execution_time = time.time() - start_time
        return {'output': '\n'.join(results), 'execution_time': execution_time}
        
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

def run_text_code(code: str) -> Dict[str, Any]:
    """Handle text content - simply return the text as output"""
    try:
        start_time = time.time()
        if not code.strip():
            execution_time = time.time() - start_time
            return {'output': '(Empty text document)', 'execution_time': execution_time}
        execution_time = time.time() - start_time
        return {'output': code, 'execution_time': execution_time}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

# Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web interface"""
    return HTMLResponse(content=HTML_TEMPLATE)

@app.post("/api/run", response_model=CodeResponse)
async def run_code(request: CodeRequest):
    """
    Execute code in the specified language
    
    - **code**: The source code to execute
    - **language**: Programming language (python, c, cpp, java, kotlin, javascript, rust, sql, text)
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided")
    
    # Security: Basic validation (only for Python)
    if request.language == 'python':
        dangerous_imports = ['os', 'subprocess', 'sys', 'eval', 'exec', '__import__']
        if any(dangerous in request.code for dangerous in dangerous_imports):
            raise HTTPException(status_code=400, detail="Potentially dangerous code detected")
    
    # Route to appropriate runner
    runners = {
        'python': run_python_code,
        'c': run_c_code,
        'cpp': run_cpp_code,
        'java': run_java_code,
        'kotlin': run_kotlin_code,
        'javascript': run_javascript_code,
        'rust': run_rust_code,
        'sql': run_sql_code,
        'text': run_text_code
    }
    
    runner = runners.get(request.language, run_python_code)
    
    # Handle async and sync runners
    if asyncio.iscoroutinefunction(runner):
        result = await runner(request.code)
    else:
        result = runner(request.code)
    
    return CodeResponse(**result)

@app.get("/api/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            {"id": "python", "name": "Python", "extension": ".py"},
            {"id": "c", "name": "C", "extension": ".c"},
            {"id": "cpp", "name": "C++", "extension": ".cpp"},
            {"id": "java", "name": "Java", "extension": ".java"},
            {"id": "kotlin", "name": "Kotlin", "extension": ".kt"},
            {"id": "javascript", "name": "JavaScript", "extension": ".js"},
            {"id": "rust", "name": "Rust", "extension": ".rs"},
            {"id": "sql", "name": "SQL", "extension": ".sql"},
            {"id": "text", "name": "Text", "extension": ".txt"}
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Online Compiler API is running"}

if __name__ == '__main__':
    import uvicorn
    print("Starting FastAPI online compiler server...")
    print("Make sure you have the required compilers installed:")
    print("- Python 3")
    print("- gcc (for C)")
    print("- g++ (for C++)")
    print("- javac and java (for Java)")
    print("- kotlinc (for Kotlin)")
    print("- node (for JavaScript)")
    print("- cargo and rustc (for Rust)")
    print("- sqlite3 (for SQL) - usually comes with Python")
    print("\nAPI Documentation will be available at: http://localhost:8000/docs")
    print("Interactive API at: http://localhost:8000/redoc")
    
    uvicorn.run(
        "fastapi_compiler:app",  # Replace "main" with your filename if different
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# # Execute:
# uvicorn fastapi_compiler:app --host 0.0.0.0 --port 8000 --reload