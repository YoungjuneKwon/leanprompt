from typing import AsyncGenerator, List, Dict, Any, Optional
from .openai import OpenAIProvider


class VLLMProvider(OpenAIProvider):
    """
    Provider for vLLM (OpenAI-compatible API).
    
    vLLM is a high-throughput and memory-efficient inference engine for LLMs.
    It provides an OpenAI-compatible API server that can be used as a drop-in
    replacement for OpenAI's API.
    
    Usage:
        lp = LeanPrompt(
            app,
            provider="vllm",
            base_url="http://localhost:8000/v1",
            api_key="your-api-key"  # Optional if server doesn't require auth
        )
    
    Server setup:
        vllm serve MODEL_NAME --dtype auto --api-key your-api-key
        # Or without authentication:
        vllm serve MODEL_NAME --dtype auto
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize vLLM provider.
        
        Args:
            base_url: The base URL of the vLLM server (e.g., "http://localhost:8000/v1")
            api_key: Optional API key for authentication. If the vLLM server was started
                    with --api-key, this must match that key. If not provided, defaults
                    to "EMPTY" which works for servers without authentication.
            **kwargs: Additional arguments passed to OpenAI client
        """
        # vLLM is fully OpenAI-compatible, so we can use the OpenAI provider directly
        # Use "EMPTY" as default API key for servers without authentication
        super().__init__(api_key=api_key or "EMPTY", base_url=base_url, **kwargs)
