## 🤖DeepSite Replica: AI-Powered Website Generator🤖

DeepSite Replica is a Streamlit-based application that leverages the `llama3.2:latest model` and `deepseek-r1:latest model` (via Ollama) to generate unique, prompt-driven website UIs. 
Users can specify a website description `(e.g., "Create a chatbot UI" or "Create a blog website")`, choose a design style `(e.g., Modern Gradient, Minimalistic)`, and select a CSS framework `(e.g., Tailwind CSS, Bootstrap)`. 
The app generates HTML, CSS, and JavaScript files, compiles them into a local directory, and serves the website via a local HTTP server for instant preview.

## Note 
This is a basic experimental model I've named `'Deepsite Replica.'` While it's inspired by Deepsite, please note that it is not intended to function at the same level—it's a simplified version incorporating an agent system for testing purposes.

## 1️⃣Features1️⃣

→Prompt-Driven UI Generation: Create websites based on natural language descriptions (e.g., portfolios, chatbots, blogs).

→Diverse Designs: Customize designs with styles (Modern Gradient, Minimalistic, Bold and Colorful, Classic) and frameworks (Tailwind CSS, Bootstrap, or none).

→Local Server Preview: View generated websites instantly via a local HTTP server with dynamic port selection.

→Error Handling: Robust fallback to a default photographer portfolio template if generation fails.

→Debug Logging: Logs saved to debug.log for troubleshooting without cluttering the UI.

→Prompt History: Reuse previous prompts for convenience.

## 📒Prerequisites📒

`Python 3.8+`: Ensure Python is installed (python.org).

`Ollama`: Install Ollama to run the llama3.2:latest model (ollama.com).

`Streamlit`: Python library for the web interface.

`Ollama Python Client`: For interacting with the Ollama server.

`Git (optional)`: For cloning the repository.

## ⬇️Installation⬇️

🗃️Clone the Repository (or download the code):
```
git clone https://github.com/your-repo/deepsite-replica.git
cd deepsite-replica
```
🗃️Install Python Dependencies:

`pip install streamlit ollama`

🗃️Install Ollama:

Download and install Ollama from ollama.com.

Start the Ollama server:

`ollama serve`

Pull the llama3.2:latest model:

`ollama pull llama3.2:latest`

Verify the model is available:

`ollama list`

🗃️Verify Setup:

Ensure the Ollama server is running on `localhost:11434`

Confirm Python and dependencies are installed:

```
python --version
pip show streamlit ollama
```

## Troubleshooting

⚠️Ollama Server Not Running: 

Ensure ollama serve is running in a terminal.

Check localhost:11434 is accessible (e.g., via curl http://localhost:11434).

⚠️Model Not Found:

Run ollama pull llama3.2:latest and verify with ollama list.

Click Force Pull Model in the app to retry pulling.

⚠️Port Conflicts:

The app automatically selects a free port (7000–7010). If it fails, free ports manually (e.g., netstat -a -n -o on Windows to find and kill processes).

⚠️Similar UI Designs:

Use specific prompts (e.g., "Use a dark theme with neon accents").

Try different styles/frameworks or check debug.log for model output issues.

⚠️Debugging:

Check debug.log in the project directory for detailed logs (e.g., model responses, errors).

Share logs when reporting issues.

## License

This project is licensed under the MIT License. See the LICENSE file for details.


## Contact

For issues or feedback:

Open an issue on the GitHub repository.

Email: `akajay14955j@gmail.com`

Happy website generating!


