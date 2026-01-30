import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from .base import BaseProvider


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        # Ollama typically doesn't require an API key for local access
        self.base_url = base_url.rstrip("/")

    async def generate_stream(
        self,
        system_prompt: str,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})

        # Ollama API: /api/chat
        payload = {
            "model": kwargs.get("model", "qwen2.5-coder"),  # Default example model
            "messages": messages,
            "stream": True,
            **{k: v for k, v in kwargs.items() if k != "model"},
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(
                        f"Ollama API error ({response.status_code}): {error_text.decode()}"
                    )

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("done"):
                            break

                        # Ollama chat response structure
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

    async def generate(
        self,
        system_prompt: str,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})

        payload = {
            "model": kwargs.get("model", "qwen2.5-coder"),
            "messages": messages,
            "stream": False,
            **{k: v for k, v in kwargs.items() if k != "model"},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama API error ({response.status_code}): {response.text}"
                )

            data = response.json()
            return data.get("message", {}).get("content", "")
