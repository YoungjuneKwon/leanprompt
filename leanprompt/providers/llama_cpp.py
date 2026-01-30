from typing import AsyncGenerator, List, Dict, Any, Optional
from .openai import OpenAIProvider


class LlamaCppProvider(OpenAIProvider):
    """
    Provider for llama-cpp-python server (OpenAI-compatible API).
    
    llama-cpp-python provides an OpenAI-compatible server that allows you to
    use local GGUF models with the same API as OpenAI.
    
    Usage:
        lp = LeanPrompt(
            app,
            provider="llama-cpp",
            base_url="http://localhost:8000/v1",
            api_key="your-api-key"  # Optional if server doesn't require auth
        )
    
    Server setup:
        python -m llama_cpp.server --model path/to/model.gguf --api-key your-api-key
        # Or without authentication:
        python -m llama_cpp.server --model path/to/model.gguf
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize llama-cpp-python provider.
        
        Args:
            base_url: The base URL of the llama-cpp server (e.g., "http://localhost:8000/v1")
            api_key: Optional API key for authentication. If the server was started with
                    --api-key, this must match that key. If not provided, defaults to
                    "EMPTY" which works for servers without authentication.
            **kwargs: Additional arguments passed to OpenAI client
        """
        # llama-cpp-python server is fully OpenAI-compatible
        # Use "EMPTY" as default API key for servers without authentication
        super().__init__(api_key=api_key or "EMPTY", base_url=base_url, **kwargs)
