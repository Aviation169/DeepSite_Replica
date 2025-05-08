import streamlit as st
import ollama
import os
import subprocess
import webbrowser
import time
import re
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import shutil
import socket

# Set up logging
logging.basicConfig(filename="debug.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Default website template (fallback)
DEFAULT_WEBSITE = {
    "html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Default Portfolio</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Photographer Portfolio</h1>
        <nav>
            <a href="#gallery">Gallery</a>
            <a href="#about">About</a>
            <a href="#contact">Contact</a>
        </nav>
    </header>
    <section id="gallery">
        <h2>Gallery</h2>
        <div class="gallery">
            <img src="https://placehold.co/300x300" alt="Photo 1">
            <img src="https://placehold.co/300x300" alt="Photo 2">
        </div>
    </section>
    <section id="about">
        <h2>About</h2>
        <p>Welcome to my photography portfolio!</p>
    </section>
    <section id="contact">
        <h2>Contact</h2>
        <form>
            <input type="text" placeholder="Name" required>
            <input type="email" placeholder="Email" required>
            <textarea placeholder="Message" required></textarea>
            <button type="submit">Send</button>
        </form>
    </section>
    <script src="script.js"></script>
</body>
</html>""",
    "css": """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}
header {
    background: #333;
    color: white;
    text-align: center;
    padding: 1em;
}
nav a {
    color: white;
    margin: 0 1em;
    text-decoration: none;
}
section {
    padding: 2em;
}
.gallery {
    display: flex;
    flex-wrap: wrap;
    gap: 1em;
    justify-content: center;
}
img {
    max-width: 100%;
    width: 300px;
    height: auto;
}
form {
    display: flex;
    flex-direction: column;
    gap: 1em;
    max-width: 400px;
}
input, textarea {
    padding: 0.5em;
}
button {
    padding: 0.5em;
    background: #333;
    color: white;
    border: none;
    cursor: pointer;
}""",
    "js": """document.querySelector('form').addEventListener('submit', (e) => {
    e.preventDefault();
    alert('This is a demo form. No data is sent.');
});"""
}

# Initialize session state
if "model_confirmed" not in st.session_state:
    st.session_state["model_confirmed"] = False
if "prompt_history" not in st.session_state:
    st.session_state["prompt_history"] = []
if "server" not in st.session_state:
    st.session_state["server"] = None

# Function to check if Ollama server is running
def check_ollama_server():
    try:
        ollama.list()
        return True
    except Exception as e:
        st.error(f"Ollama server not running: {str(e)}. Please start the server with `ollama serve` and ensure it's running on localhost:11434.")
        return False

# Function to check if model exists and pull if missing
def ensure_model(model_name="llama3.2:latest"):
    if st.session_state["model_confirmed"]:
        logging.debug(f"Model {model_name} already confirmed in session state.")
        return True

    if not shutil.which("ollama"):
        st.error("Ollama command not found. Please install Ollama from https://ollama.com and ensure it's in your PATH.")
        return False

    if not check_ollama_server():
        return False

    try:
        response = ollama.list()
        models = response.get("models", [])
        for model in models:
            if model_name.lower() in model.model.lower():
                logging.debug(f"Found model {model.model} matching {model_name}")
                st.session_state["model_confirmed"] = True
                return True

        st.info(f"Model {model_name} not found. Pulling it now...")
        process = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            check=True
        )
        logging.debug(f"Pull command output: {process.stdout}\nErrors: {process.stderr}")
        response = ollama.list()
        models = response.get("models", [])
        for model in models:
            if model_name.lower() in model.model.lower():
                st.success(f"Model {model_name} pulled successfully!")
                st.session_state["model_confirmed"] = True
                return True
        st.error(f"Model {model_name} not detected after pulling. Verify with `ollama list`.")
        return False
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to pull model {model_name}: {e.stderr}")
        logging.error(f"Failed to pull model {model_name}: {e.stderr}\nCommand output: {e.stdout}")
        return False
    except Exception as e:
        st.error(f"Error checking model: {str(e)}")
        logging.error(f"Error checking model: {str(e)}")
        return False

# Function to select example based on prompt
def get_example(prompt):
    prompt = prompt.lower()
    if "chatbot" in prompt:
        return {
            "html": """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Chatbot</title><link rel="stylesheet" href="styles.css"></head><body><div class="chat-container"><div class="chat-history" id="chatHistory"></div><input type="text" id="messageInput" placeholder="Type a message"><button onclick="sendMessage()">Send</button></div><script src="script.js"></script></body></html>""",
            "css": """body { font-family: 'Roboto', sans-serif; background: linear-gradient(to bottom, #e0f7fa, #80deea); } .chat-container { max-width: 600px; margin: 2em auto; padding: 1em; background: white; border-radius: 10px; } .chat-history { height: 300px; overflow-y: auto; margin-bottom: 1em; } input { width: 80%; padding: 0.5em; } button { padding: 0.5em 1em; background: #0288d1; color: white; border: none; }""",
            "js": """function sendMessage() { const input = document.getElementById('messageInput'); const history = document.getElementById('chatHistory'); const message = input.value; if (message) { const msgDiv = document.createElement('div'); msgDiv.textContent = 'User: ' + message; history.appendChild(msgDiv); input.value = ''; history.scrollTop = history.scrollHeight; } }"""
        }
    elif "blog" in prompt:
        return {
            "html": """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Blog</title><link rel="stylesheet" href="styles.css"></head><body><header><h1>My Blog</h1></header><main><article><h2>Post Title</h2><p>Post content...</p></article><section class="comments"><h3>Comments</h3><form><input type="text" placeholder="Add a comment"><button type="submit">Post</button></form></section></main><script src="script.js"></script></body></html>""",
            "css": """body { font-family: 'Georgia', serif; margin: 0; background: #f5f5f5; } header { background: #d81b60; color: white; text-align: center; padding: 1em; } main { max-width: 800px; margin: 2em auto; } article { background: white; padding: 1em; margin-bottom: 1em; } .comments { background: #ffebee; padding: 1em; } input { padding: 0.5em; width: 70%; } button { padding: 0.5em; background: #d81b60; color: white; border: none; }""",
            "js": """document.querySelector('form').addEventListener('submit', (e) => { e.preventDefault(); alert('Comment posted!'); });"""
        }
    else:
        return {
            "html": """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Portfolio</title><link rel="stylesheet" href="styles.css"></head><body><header><h1>Portfolio</h1></header><section><h2>Welcome</h2><p>This is my portfolio.</p></section><script src="script.js"></script></body></html>""",
            "css": """body { font-family: 'Helvetica', sans-serif; background: #e8eaf6; margin: 0; } header { background: #3f51b5; color: white; text-align: center; padding: 1em; } section { max-width: 600px; margin: 2em auto; background: white; padding: 1em; border-radius: 5px; }""",
            "js": """console.log('Portfolio loaded');"""
        }

# Function to extract code from model response
def extract_code(content):
    content = re.sub(r'<think>.*?</think>|<think>|</think>', '', content, flags=re.DOTALL)
    content = content.strip()
    sections = re.split(r'---(HTML|CSS|JS)---\n', content)
    code = {}
    for i in range(1, len(sections), 2):
        section_type = sections[i].lower()
        section_content = sections[i+1].strip()
        code[section_type] = section_content
    logging.debug(f"Extracted code: {code}")
    missing = [key for key in ["html", "css", "js"] if key not in code]
    if missing:
        logging.debug(f"Missing sections: {', '.join(missing)}")
        return None
    for key, value in code.items():
        if not value.strip():
            logging.debug(f"Empty section: {key}")
            return None
    return code

# Function to generate website code using llama3.2:latest
def generate_website_code(prompt, style, framework):
    example = get_example(prompt)
    framework_instruction = ""
    if framework == "Tailwind CSS":
        framework_instruction = """Use Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>) for styling instead of a separate styles.css file. Include Tailwind classes in the HTML and minimize custom CSS."""
    elif framework == "Bootstrap":
        framework_instruction = """Use Bootstrap 5 via CDN (<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"> and <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>) for styling and interactivity. Use Bootstrap classes in the HTML and minimize custom CSS and JS."""
    
    full_prompt = f"""
    You are an expert web developer. Based on the following description, generate a complete website with:
    - An HTML file (index.html) with semantic structure, linking to external styles.css and script.js (unless using a CSS framework).
    - A CSS file (styles.css) for styling, using modern design principles (e.g., flexbox, responsive design), unless a framework is specified.
    - A JavaScript file (script.js) for interactivity (e.g., event listeners, animations).
    {framework_instruction}
    Return the raw code for each file, separated by delimiters as follows:
    ---HTML---
    <!DOCTYPE html><html lang="en">...</html>
    ---CSS---
    body {{ font-family: Arial; ... }}
    ---JS---
    console.log('Hello');
    Do not include markdown, code fences, explanations, or tags like <think>. Use only the delimiters above to separate the code sections.
    Ensure the code is functional, error-free, and visually appealing. The design should reflect the specified style ({style}) and be unique, avoiding similarity to the example or default portfolio unless the prompt explicitly requests it.
    For example, a chatbot UI should have a message input and chat history with a modern layout, while a blog should have articles and comments with a distinct aesthetic.
    Example (use as inspiration, not a template):
    ---HTML---
    {example["html"]}
    ---CSS---
    {example["css"]}
    ---JS---
    {example["js"]}
    Description: {prompt}
    """
    try:
        response = ollama.chat(
            model="llama3.2:latest",
            messages=[{"role": "user", "content": full_prompt}],
            options={"temperature": 0.8}
        )
        content = response["message"]["content"]
        logging.debug(f"Raw model response: {content[:500]}... (truncated)" if len(content) > 500 else content)
        code = extract_code(content)
        if code and all(key in code for key in ["html", "css", "js"]):
            logging.debug(f"Parsed code: {code}")
            if framework != "None" and not code["css"].strip():
                code["css"] = "/* Framework styles applied in HTML */"
            return code
        st.warning("Invalid response format. Retrying...")
        response = ollama.chat(
            model="llama3.2:latest",
            messages=[{"role": "user", "content": full_prompt}],
            options={"temperature": 0.8}
        )
        content = response["message"]["content"]
        code = extract_code(content)
        if code and all(key in code for key in ["html", "css", "js"]):
            logging.debug(f"Parsed code: {code}")
            if framework != "None" and not code["css"].strip():
                code["css"] = "/* Framework styles applied in HTML */"
            return code
        st.error("Failed to generate website code. Using default template.")
        logging.debug("Falling back to default template due to generation failure.")
        return {"error": "Model response failure", "raw": content}
    except Exception as e:
        st.warning(f"Generation failed: {str(e)}. Using default template.")
        logging.warning(f"Generation failed: {str(e)}")
        return {"error": "Model response failure", "raw": ""}

# Agent to compile and save website files
def compile_website(code, output_dir="output"):
    if "error" in code:
        return code["error"]
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        if not os.access(output_dir, os.W_OK):
            return "Error: Output directory is not writable."
        
        for file_name, content in [("index.html", code["html"]), 
                                 ("styles.css", code["css"]), 
                                 ("script.js", code["js"])]:
            if not content:
                return f"Error: {file_name} content is empty."
            with open(os.path.join(output_dir, file_name), "w", encoding="utf-8") as f:
                f.write(content)
        
        return "Website compiled successfully!"
    except OSError as e:
        return f"File system error: {str(e)}"

# Function to find a free port
def find_free_port(start_port=7000, max_attempts=10):
    port = start_port
    for _ in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1
    return None

# Function to stop the server
def stop_server():
    if st.session_state["server"]:
        st.session_state["server"].shutdown()
        st.session_state["server"].server_close()
        st.session_state["server"] = None
        st.success("Server stopped.")
    else:
        st.warning("No server is running.")

# Function to start a local server
def start_server():
    port = find_free_port()
    if not port:
        st.error("No free ports available. Please free a port and try again.")
        return None
    
    if not os.path.exists("output"):
        st.error("Output directory not found. Please generate the website first.")
        return None
    
    os.chdir("output")
    server = HTTPServer(("", port), SimpleHTTPRequestHandler)
    st.session_state["server"] = server
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return port

# Streamlit UI
st.title("DeepSite Replica: AI-Powered Website Generator")
st.write("Enter a description and customize the style to generate a unique website using Llama3.2!")

# User input with customization
st.subheader("Website Customization")
col1, col2 = st.columns(2)
with col1:
    style = st.selectbox("Design Style", ["Modern Gradient", "Minimalistic", "Bold and Colorful", "Classic"])
with col2:
    framework = st.selectbox("CSS Framework", ["None", "Tailwind CSS", "Bootstrap"])

prompt = st.selectbox("Select or Edit Prompt", [""] + st.session_state["prompt_history"], index=0, format_func=lambda x: "New Prompt" if x == "" else x)
prompt_input = st.text_area("Website Description", value=prompt or "Create a portfolio website for a photographer with a gallery, about section, and contact form.", height=100)
if prompt_input and prompt_input not in st.session_state["prompt_history"]:
    st.session_state["prompt_history"].insert(0, prompt_input)
    if len(st.session_state["prompt_history"]) > 10:
        st.session_state["prompt_history"] = st.session_state["prompt_history"][:10]

# Force pull model option
if st.button("Force Pull Model"):
    with st.spinner("Pulling llama3.2:latest..."):
        try:
            process = subprocess.run(
                ["ollama", "pull", "llama3.2:latest"],
                capture_output=True,
                text=True,
                check=True
            )
            logging.debug(f"Pull command output: {process.stdout}\nErrors: {process.stderr}")
            st.session_state["model_confirmed"] = False
            st.success("Model llama3.2:latest pulled successfully!")
        except subprocess.CalledProcessError as e:
            st.error(f"Failed to pull model: {e.stderr}")
            logging.error(f"Failed to pull model: {e.stderr}\nCommand output: {e.stdout}")

# Generate button
if st.button("Generate Website"):
    with st.spinner("Checking model availability..."):
        if not ensure_model():
            st.stop()
    
    with st.spinner("Generating website code..."):
        code = generate_website_code(prompt_input, style, framework)
        
        if "error" in code:
            st.error(code["error"])
            st.warning("Using default website template due to generation failure.")
            code = DEFAULT_WEBSITE
        
        st.subheader("Generated Code")
        st.code(code["html"], language="html")
        st.code(code["css"], language="css")
        st.code(code["js"], language="javascript")
        
        result = compile_website(code)
        if "successfully" in result:
            st.success(result)
            
            with st.spinner("Starting local server..."):
                stop_server()  # Ensure any existing server is stopped
                port = start_server()
                if port:
                    preview_url = f"http://localhost:{port}"
                    st.write(f"Preview your website at: [{preview_url}]({preview_url})")
                    try:
                        webbrowser.open(preview_url)
                    except Exception as e:
                        st.warning(f"Failed to open browser: {str(e)}. Please manually visit {preview_url}.")
                    st.markdown(f'<iframe src="{preview_url}" width="100%" height="600"></iframe>', 
                               unsafe_allow_html=True)
                else:
                    st.error("Failed to start server.")
        else:
            st.error(result)

# Stop server button
if st.button("Stop Server"):
    stop_server()

# Instructions in expander
with st.sidebar.expander("Setup Instructions"):
    st.write("1. **Install Ollama**: Download from [ollama.com](https://ollama.com) and follow the setup guide.")
    st.write("2. **Start Ollama Server**: Run `ollama serve` in a terminal to start the server.")
    st.write("3. **Pull Model**: Run `ollama pull llama3.2:latest` in a terminal. Verify with `ollama list`.")
    st.write("4. **Install Dependencies**: Run `pip install streamlit ollama` in your terminal.")
    st.write("5. **Run App**: Save this script as `app.py` and run `streamlit run app.py`.")
    st.write("6. **Troubleshooting**:")
    st.write("- Ensure Ollama server is running (`ollama serve`).")
    st.write("- Verify model name with `ollama list`. If missing, pull it manually.")
    st.write("- Check network connectivity for model pulling.")
    st.write("- If code generation produces similar designs, try a more specific prompt or different style/framework.")