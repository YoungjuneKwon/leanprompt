"""
Example demonstrating how to use LeanPrompt with vLLM and llama-cpp-python providers.

vLLM and llama-cpp-python both provide OpenAI-compatible APIs, making them
easy drop-in replacements for OpenAI's API while running models locally.

Prerequisites:
    For vLLM:
        pip install vllm
        vllm serve MODEL_NAME --dtype auto --api-key your-key
    
    For llama-cpp-python:
        pip install 'llama-cpp-python[server]'
        python -m llama_cpp.server --model path/to/model.gguf --api-key your-key
"""

from fastapi import FastAPI
from leanprompt import LeanPrompt, Guard
from pydantic import BaseModel
import uvicorn
import os


class MoodAnalysis(BaseModel):
    mood: str
    confidence: float


app = FastAPI()

# Choose your provider:
provider_type = os.getenv("PROVIDER", "vllm")  # vllm, llama-cpp, or openai

if provider_type == "vllm":
    # Example 1: Using vLLM (high-performance local inference)
    lp = LeanPrompt(
        app,
        provider="vllm",
        base_url="http://localhost:8000/v1",
        api_key=os.getenv("VLLM_API_KEY"),  # Optional if server has no auth
        prompt_dir="examples/prompts",
    )
elif provider_type == "llama-cpp":
    # Example 2: Using llama-cpp-python (GGUF models)
    lp = LeanPrompt(
        app,
        provider="llama-cpp",
        base_url="http://localhost:8000/v1",
        api_key=os.getenv("LLAMA_CPP_API_KEY"),  # Optional if server has no auth
        prompt_dir="examples/prompts",
    )
else:
    # Example 3: Using OpenAI for comparison
    lp = LeanPrompt(
        app,
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        prompt_dir="examples/prompts",
    )


@lp.route("/analyze", prompt_file="mood_json.md")
@Guard.validate(MoodAnalysis)
async def analyze_mood(user_input: str):
    """
    Analyzes the mood from user input.
    Works with any provider (vLLM, llama-cpp, or OpenAI).
    """
    pass


if __name__ == "__main__":
    print(f"Starting server with provider: {provider_type}")
    print(f"Test endpoint: POST http://localhost:8000/analyze")
    print(f'Example: curl -X POST "http://localhost:8000/analyze" -H "Content-Type: application/json" -d \'{{"message": "I am feeling great today!"}}\'')
    uvicorn.run(app, host="0.0.0.0", port=8000)
