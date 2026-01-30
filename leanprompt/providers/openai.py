import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.api_key = api_key
        self.base_url = base_url

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

        payload = {
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "messages": messages,
            "stream": True,
            **{k: v for k, v in kwargs.items() if k != "model"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(
                        f"OpenAI API error ({response.status_code}): {error_text.decode()}"
                    )

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            chunk = data["choices"][0]["delta"].get("content", "")
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
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "messages": messages,
            "stream": False,
            **{k: v for k, v in kwargs.items() if k != "model"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"OpenAI API error ({response.status_code}): {response.text}"
                )

            data = response.json()
            return data["choices"][0]["message"]["content"]
