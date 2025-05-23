import tkinter as tk
from tkinter import scrolledtext, ttk
import requests
import os
import subprocess
from pathlib import Path
import re
import time

# File System Setup
WORKING_DIR = "workspace"
Path(WORKING_DIR).mkdir(exist_ok=True)
TASK_HISTORY = []

# Ollama API Call with Retry
def call_ollama(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "deepseek-r1:7b",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.RequestException as e:
            append_output(f"AI Agent Error (Attempt {attempt+1}/{retries}): {e}. Ensure Ollama is running (OLLAMA_ORIGINS=* ollama serve).")
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None

# Parse LLM Response
def parse_llm_response(response, type):
    if not response:
        return None
    regex = r"```.*?\n([\s\S]*?)\n```"
    match = re.search(regex, response)
    content = match.group(1).strip() if match else response.strip()
    if type == "filename":
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', content.lower())
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        if not sanitized:
            return None
        return f"{sanitized}.html"
    elif type == "code":
        return content if content.strip() else None
    return content

# Initialize Git Repository and Project Structure
def init_git_repo():
    git_dir = f"{WORKING_DIR}/.git"
    if not os.path.exists(git_dir):
        try:
            subprocess.run(["git", "init"], cwd=WORKING_DIR, check=True, capture_output=True, text=True)
            with open(f"{WORKING_DIR}/README.md", "w") as f:
                f.write("# HTML Project Workspace\nGenerated by AI Agent")
            with open(f"{WORKING_DIR}/.gitignore", "w") as f:
                f.write("*.pyc\n__pycache__/\nnode_modules/\n")
            append_output("AI Agent: Initialized Git repository and project structure in workspace")
        except subprocess.CalledProcessError as e:
            append_output(f"AI Agent: Failed to initialize Git repository: {e.stderr}")
        except FileNotFoundError:
            append_output("AI Agent: Git not found. Ensure 'git' is installed and in your PATH.")

# AI Agent: Create File
def create_file(task):
    prompt = f'Suggest an HTML filename for the task "{task}" (e.g., "index.html"). Return only the filename inside triple backticks, no extra text:\n```\nfilename\n```'
    response = call_ollama(prompt)
    append_output(f"AI Agent: Raw filename response: {response}")
    filename = parse_llm_response(response, "filename")
    if not filename:
        filename = f"task_{int(time.time())}.html"
        append_output("AI Agent: Fallback filename used due to invalid or missing AI response.")
    file_path = f"{WORKING_DIR}/{filename}"
    try:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("")
            append_output(f"AI Agent: Created file {filename}")
            return filename
        append_output(f"AI Agent: File {filename} already exists.")
        return None
    except OSError as e:
        append_output(f"AI Agent: Invalid filename {filename}: {e}. Using fallback.")
        filename = f"task_{int(time.time())}.html"
        file_path = f"{WORKING_DIR}/{filename}"
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("")
            append_output(f"AI Agent: Created fallback file {filename}")
            return filename
        append_output(f"AI Agent: Fallback file {filename} already exists.")
        return None

# AI Agent: Write HTML Code with Inline CSS/JS
def write_code(task, filename):
    prompt = f'''
Write HTML code for the task "{task}" to be saved in {filename}. Include inline CSS in <style> tags and JavaScript in <script> tags within the HTML. Return only the code inside triple backticks, no extra text. Example:
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sample Page</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; }}
        h1 {{ color: blue; }}
    </style>
</head>
<body>
    <h1>Hello, World!</h1>
    <script>
        console.log("Page loaded!");
    </script>
</body>
</html>
```
For task "{task}":
```
code
```
'''
    response = call_ollama(prompt)
    append_output(f"AI Agent: Raw code response: {response}")
    code = parse_llm_response(response, "code")
    if not code:
        code = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Empty Page</title>
    <style>
        body { font-family: Arial, sans-serif; }
    </style>
</head>
<body>
    <h1>Empty Page</h1>
    <script>
        console.log("Empty page loaded");
    </script>
</body>
</html>
'''
        append_output("AI Agent: Fallback code used due to invalid or missing AI response.")
    file_path = f"{WORKING_DIR}/{filename}"
    with open(file_path, "w") as f:
        f.write(code)
    append_output(f"AI Agent: Wrote code to {filename}")
    with open(f"{WORKING_DIR}/task_log.txt", "a") as log:
        log.write(f"Task: {task}\nFile: {filename}\nTimestamp: {time.ctime()}\n\n")
    append_output("AI Agent: Logged task to task_log.txt")
    return code

# Run Live Server
def run_live_server(filename):
    try:
        code_paths = [
            "code",
            r"C:\Program Files\Microsoft VS Code\bin\code",
            r"C:\Users\AJAYSI~1\AppData\Local\Programs\Microsoft VS Code\bin\code"
        ]
        for code_cmd in code_paths:
            try:
                subprocess.run([code_cmd, "--version"], capture_output=True, check=True, text=True)
                subprocess.run([code_cmd, "--new-window", "--folder-uri", f"file://{os.path.abspath(WORKING_DIR)}"], check=True)
                tasks_json = f"{WORKING_DIR}/.vscode/tasks.json"
                os.makedirs(f"{WORKING_DIR}/.vscode", exist_ok=True)
                with open(tasks_json, "w") as f:
                    f.write('''
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Live Server",
            "type": "shell",
            "command": "code --command live-server.goLive",
            "group": {
                "kind": "build",
                "isDefault": true
            }
        }
    ]
}
                    ''')
                subprocess.run([code_cmd, "--folder-uri", f"file://{os.path.abspath(WORKING_DIR)}", "--command", "workbench.action.tasks.runTask", "Live Server"], check=True)
                append_output(f"AI Agent: Started Live Server for {filename}")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        raise FileNotFoundError("VS Code CLI not found")
    except subprocess.CalledProcessError as e:
        append_output(f"AI Agent: Failed to start Live Server: {e.stderr}. Ensure Live Server extension is installed.")
    except FileNotFoundError:
        append_output("AI Agent: VS Code CLI not found for Live Server. Ensure 'code' is in your PATH.\n"
                      "1. Install VS Code: https://code.visualstudio.com/\n"
                      "2. Install Live Server extension: Search 'Live Server' in VS Code Extensions\n"
                      "3. Add to PATH: Add 'C:\\Program Files\\Microsoft VS Code\\bin' or 'C:\\Users\\AJAYSI~1\\AppData\\Local\\Programs\\Microsoft VS Code\\bin'\n"
                      "4. For Anaconda: Run 'set PATH=%PATH%;C:\\Program Files\\Microsoft VS Code\\bin' in Anaconda Prompt\n"
                      "5. Verify: Run 'code --version'\n"
                      "See: https://code.visualstudio.com/docs/setup/setup-overview")

# Open VS Code in New Window
def open_vscode(filename):
    file_path = f"{WORKING_DIR}/{filename}"
    try:
        code_paths = [
            "code",
            r"C:\Program Files\Microsoft VS Code\bin\code",
            r"C:\Users\AJAYSI~1\AppData\Local\Programs\Microsoft VS Code\bin\code"
        ]
        for code_cmd in code_paths:
            try:
                subprocess.run([code_cmd, "--version"], capture_output=True, check=True, text=True)
                subprocess.run([code_cmd, "--new-window", "--folder-uri", f"file://{os.path.abspath(WORKING_DIR)}", file_path], check=True)
                append_output(f"AI Agent: Opened {filename} in a new VS Code window (workspace: {WORKING_DIR})")
                run_button.config(state='normal')
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        raise FileNotFoundError("VS Code CLI not found")
    except subprocess.CalledProcessError as e:
        append_output(f"AI Agent: Failed to open VS Code: {e.stderr}")
        run_button.config(state='disabled')
    except FileNotFoundError:
        append_output("AI Agent: VS Code CLI not found. Ensure 'code' is in your PATH.\n"
                      "1. Install VS Code: https://code.visualstudio.com/\n"
                      "2. Add to PATH: Add 'C:\\Program Files\\Microsoft VS Code\\bin' or 'C:\\Users\\AJAYSI~1\\AppData\\Local\\Programs\\Microsoft VS Code\\bin'\n"
                      "3. For Anaconda: Run 'set PATH=%PATH%;C:\\Program Files\\Microsoft VS Code\\bin' in Anaconda Prompt\n"
                      "4. Verify: Run 'code --version'\n"
                      "5. Check VS Code settings: Ensure 'window.openFilesInNewWindow' is 'on' in Settings or settings.json\n"
                      "See: https://code.visualstudio.com/docs/setup/setup-overview")

# Execute Task
def execute_task():
    task = task_input.get()
    if not task:
        append_output("AI Agent: Please enter a task.")
        return
    append_output(f"AI Agent: Processing task: {task}")
    if task not in TASK_HISTORY:
        TASK_HISTORY.append(task)
        task_dropdown['values'] = TASK_HISTORY

    # Step 1: Initialize Git Repository
    init_git_repo()

    # Step 2: Create File
    filename = create_file(task)
    if not filename:
        return

    # Step 3: Write Code
    code = write_code(task, filename)
    if not code:
        return

    # Step 4: Open VS Code in New Window
    open_vscode(filename)

# Clear Chat Output
def clear_output():
    chat_output.config(state='normal')
    chat_output.delete(1.0, tk.END)
    chat_output.config(state='disabled')
    run_button.config(state='disabled')

# Load Task from History
def load_task(event):
    task = task_dropdown.get()
    if task:
        task_input.delete(0, tk.END)
        task_input.insert(0, task)

# Append to Chat Output
def append_output(message):
    chat_output.config(state='normal')
    chat_output.insert(tk.END, f"{message}\n")
    chat_output.see(tk.END)
    chat_output.config(state='disabled')

# ChatBot UI
root = tk.Tk()
root.title("Blackbox AI-like VS Code Agent (HTML)")
root.geometry("700x500")
root.configure(bg="#252526")

# Task Input Frame
input_frame = tk.Frame(root, bg="#252526")
input_frame.pack(pady=10, padx=10, fill='x')
task_label = tk.Label(input_frame, text="Enter Task:", bg="#252526", fg="#d4d4d4", font=("Consolas", 12))
task_label.pack(side='left', padx=5)
task_input = tk.Entry(input_frame, width=50, bg="#333333", fg="#d4d4d4", insertbackground="#d4d4d4", font=("Consolas", 12))
task_input.pack(side='left', padx=5)
execute_button = tk.Button(input_frame, text="Execute", command=execute_task, bg="#007acc", fg="white", font=("Consolas", 12))
execute_button.pack(side='left', padx=5)

# Task History Dropdown
task_dropdown = ttk.Combobox(root, values=TASK_HISTORY, width=60, font=("Consolas", 12))
task_dropdown.pack(pady=5)
task_dropdown.bind('<<ComboboxSelected>>', load_task)
task_dropdown.configure(state='readonly')

# Run and Clear Buttons
button_frame = tk.Frame(root, bg="#252526")
button_frame.pack(pady=5)
run_button = tk.Button(button_frame, text="Run Live Server", command=lambda: run_live_server(task_dropdown.get() if task_dropdown.get() else task_input.get()), state='disabled', bg="#007acc", fg="white", font=("Consolas", 12))
run_button.pack(side='left', padx=5)
clear_button = tk.Button(button_frame, text="Clear Output", command=clear_output, bg="#007acc", fg="white", font=("Consolas", 12))
clear_button.pack(side='left', padx=5)

# Chat Output
chat_output = scrolledtext.ScrolledText(root, height=20, width=80, state='disabled', wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 12))
chat_output.pack(pady=10, padx=10)

# Start UI
root.mainloop()