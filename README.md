# LeanPrompt (Backend)

**LeanPrompt** is an engineering-centric LLM integration framework based on FastAPI. It helps you use LLMs as reliable and predictable software components, not just text generators.

## ✨ Key Features

* **FastAPI Native:** Integrates instantly into existing FastAPI apps as a plugin.
* **Markdown-Driven Prompts:** Manage prompts as `.md` files, separated from code. Filenames become API paths.
* **Session-Based Context Caching:** Saves token costs by sending prompts only at the start of a session and then sending only input deltas.
* **Output Guardrails:** Built-in output validation and automatic retry logic via Pydantic models.
* **WebSocket First:** Highly optimized WebSocket support for real-time streaming feedback.

## 🚀 Quick Start

### Installation

```bash
pip install leanprompt
```

### Usage

```python
from fastapi import FastAPI
from leanprompt import LeanPrompt, Guard
from pydantic import BaseModel

app = FastAPI()
lp = LeanPrompt(app, provider="openai", api_key="your_api_key_here")

class ResponseModel(BaseModel):
    answer: str
    confidence: float

# Create /ask route by loading prompts/ask_me.md
@lp.route("/ask", prompt_file="ask_me.md")
@Guard.validate(ResponseModel)
async def handle_ask(user_input: str):
    pass # The return value is handled by LeanPrompt logic
```

### Using Local LLM (Ollama)

You can use local LLMs like Qwen 2.5 Coder or DeepSeek-Coder-V2 via [Ollama](https://ollama.com).

1.  Install and run Ollama:
    ```bash
    ollama run qwen2.5-coder
    ```

2.  Initialize LeanPrompt with `ollama` provider:
    ```python
    lp = LeanPrompt(
        app, 
        provider="ollama", 
        base_url="http://localhost:11434", # Optional, defaults to this
        model="qwen2.5-coder" # Specify the model name here or in prompt frontmatter
    )
    ```

## 📂 Project Structure

```
leanprompt/
├── leanprompt/          # Main library code
│   ├── core.py          # Core logic (FastAPI integration)
│   ├── guard.py         # Validation logic
│   └── providers/       # LLM provider implementations
├── examples/            # Usage examples
│   ├── main.py          # Example FastAPI app
│   └── prompts/         # Example prompt files
├── tests/               # Unit tests
├── setup.py             # Package installation script
└── requirements.txt     # Dependencies
```

## 🏃 Running the Example

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set Environment Variable:**
    ```bash
    export LEANPROMPT_LLM_KEY="your_openai_api_key"
    ```

3.  **Run the Example Server:**
    ```bash
    # Run from the root directory
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    python examples/main.py
    ```

4.  **Test the Endpoints:**

    *   **Calculation (Add):**
        ```bash
        curl -X POST "http://localhost:8000/calc/add" \
             -H "Content-Type: application/json" \
             -d '{"message": "50 + 50"}'
        ```

    *   **Calculation (Multiply):**
        ```bash
        curl -X POST "http://localhost:8000/calc/multiply" \
             -H "Content-Type: application/json" \
             -d '{"message": "10 * 5"}'
        ```

    *   **Mood Analysis (JSON):**
        ```bash
        curl -X POST "http://localhost:8000/mood/json" \
             -H "Content-Type: application/json" \
             -d '{"message": "I am feeling great today!"}'
        ```

    *   **Mood Analysis (YAML):**
        ```bash
        curl -X POST "http://localhost:8000/mood/yaml" \
             -H "Content-Type: application/json" \
             -d '{"message": "I am a bit tired."}'
        ```
