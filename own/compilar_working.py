from flask import Flask, render_template_string, request, jsonify
import subprocess
import tempfile
import os
import signal
from threading import Timer

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Online Compiler</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .editor { width: 100%; height: 300px; font-family: monospace; }
        .output { 
            background: #f0f0f0; 
            padding: 10px; 
            border-radius: 5px; 
            white-space: pre-wrap;
            font-family: monospace;
            min-height: 100px;
            margin-top: 10px;
        }
        button { 
            padding: 10px 20px; 
            background: #007cba; 
            color: white; 
            border: none; 
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #005a87; }
        select { padding: 8px; margin: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Online Compiler</h1>
        
        <div>
            <label>Language:</label>
            <select id="language">
                <option value="python">Python</option>
                <option value="cpp">C++</option>
                <option value="java">Java</option>
                <option value="javascript">JavaScript</option>
            </select>
        </div>
        
        <textarea id="code" class="editor" placeholder="Enter your code here...">
# Python example
print("Hello, World!")
for i in range(3):
    print(f"Count: {i}")
        </textarea>
        
        <div>
            <button onclick="runCode()">Run Code</button>
            <button onclick="clearOutput()">Clear Output</button>
        </div>
        
        <div id="output" class="output">Output will appear here...</div>
    </div>

    <script>
        async function runCode() {
            const code = document.getElementById('code').value;
            const language = document.getElementById('language').value;
            const output = document.getElementById('output');
            
            output.textContent = 'Running...';
            
            try {
                const response = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, language: language })
                });
                
                const result = await response.json();
                output.textContent = result.output || result.error;
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            }
        }
        
        function clearOutput() {
            document.getElementById('output').textContent = 'Output will appear here...';
        }
        
        // Update placeholder based on language
        document.getElementById('language').addEventListener('change', function() {
            const examples = {
                python: '# Python example\\nprint("Hello, World!")\\nfor i in range(3):\\n    print(f"Count: {i}")',
                cpp: '// C++ example\\n#include <iostream>\\nusing namespace std;\\n\\nint main() {\\n    cout << "Hello, World!" << endl;\\n    return 0;\\n}',
                java: '// Java example\\npublic class Main {\\n    public static void main(String[] args) {\\n        System.out.println("Hello, World!");\\n    }\\n}',
                javascript: '// JavaScript example\\nconsole.log("Hello, World!");\\nfor(let i = 0; i < 3; i++) {\\n    console.log(`Count: ${i}`);\\n}'
            };
            document.getElementById('code').value = examples[this.value];
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

def run_python_code(code):
    """Execute Python code safely"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        process = subprocess.Popen(
            ['python3', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Set timeout
        timer = Timer(5.0, timeout_handler, [process])
        timer.start()
        
        stdout, stderr = process.communicate()
        timer.cancel()
        
        os.unlink(temp_file)
        
        if stderr:
            return {'error': stderr}
        return {'output': stdout}
        
    except Exception as e:
        return {'error': str(e)}

def run_cpp_code(code):
    """Compile and execute C++ code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(code)
            cpp_file = f.name
        
        exe_file = cpp_file.replace('.cpp', '')
        
        # Compile
        compile_process = subprocess.run(
            ['g++', cpp_file, '-o', exe_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if compile_process.returncode != 0:
            os.unlink(cpp_file)
            return {'error': f'Compilation Error:\n{compile_process.stderr}'}
        
        # Execute
        run_process = subprocess.run(
            [exe_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Cleanup
        os.unlink(cpp_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if run_process.stderr:
            return {'error': run_process.stderr}
        return {'output': run_process.stdout}
        
    except subprocess.TimeoutExpired:
        return {'error': 'Code execution timed out'}
    except Exception as e:
        return {'error': str(e)}

def run_java_code(code):
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
        compile_process = subprocess.run(
            ['javac', correct_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if compile_process.returncode != 0:
            os.unlink(correct_file)
            return {'error': f'Compilation Error:\n{compile_process.stderr}'}
        
        # Execute
        class_dir = os.path.dirname(correct_file)
        run_process = subprocess.run(
            ['java', '-cp', class_dir, class_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Cleanup
        os.unlink(correct_file)
        class_file = correct_file.replace('.java', '.class')
        if os.path.exists(class_file):
            os.unlink(class_file)
        
        if run_process.stderr:
            return {'error': run_process.stderr}
        return {'output': run_process.stdout}
        
    except subprocess.TimeoutExpired:
        return {'error': 'Code execution timed out'}
    except Exception as e:
        return {'error': str(e)}

def run_javascript_code(code):
    """Execute JavaScript code using Node.js"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            js_file = f.name
        
        process = subprocess.run(
            ['node', js_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        os.unlink(js_file)
        
        if process.stderr:
            return {'error': process.stderr}
        return {'output': process.stdout}
        
    except subprocess.TimeoutExpired:
        return {'error': 'Code execution timed out'}
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if not code.strip():
        return jsonify({'error': 'No code provided'})
    
    # Security: Basic validation
    dangerous_imports = ['os', 'subprocess', 'sys', 'eval', 'exec', '__import__']
    if any(dangerous in code for dangerous in dangerous_imports):
        return jsonify({'error': 'Potentially dangerous code detected'})
    
    # Route to appropriate runner
    runners = {
        'python': run_python_code,
        'cpp': run_cpp_code,
        'java': run_java_code,
        'javascript': run_javascript_code
    }
    
    runner = runners.get(language, run_python_code)
    result = runner(code)
    
    return jsonify(result)

if __name__ == '__main__':
    print("Starting online compiler server...")
    print("Make sure you have the required compilers installed:")
    print("- Python 3")
    print("- g++ (for C++)")
    print("- javac and java (for Java)")
    print("- node (for JavaScript)")
    
    app.run(debug=True, host='0.0.0.0', port=5003)