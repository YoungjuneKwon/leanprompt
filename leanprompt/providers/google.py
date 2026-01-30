import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from .base import BaseProvider


class GoogleProvider(BaseProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ):
        if not api_key:
            raise ValueError("Google API key is required.")
        self.api_key = api_key
        self.base_url = base_url

    async def generate_stream(
        self,
        system_prompt: str,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        # Google's API format is different (Gemini)
        # Assuming v1beta/models/gemini-pro:streamGenerateContent

        contents = []
        # Convert history
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # System prompt is often passed as setup or first user message in Gemini context,
        # but for simplicity let's prepend it as user instruction or system instruction if supported.
        # Gemini 1.5 supports system_instruction.

        # Current User Input
        contents.append({"role": "user", "parts": [{"text": user_input}]})

        model = kwargs.get("model", "gemini-pro")

        url = f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}"

        payload = {
            "contents": contents,
            # System instruction support for newer models
            "system_instruction": {"parts": [{"text": system_prompt}]},
            **{k: v for k, v in kwargs.items() if k != "model"},
        }

        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", url, json=payload, headers=headers, timeout=60.0
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(
                        f"Google API error ({response.status_code}): {error_text.decode()}"
                    )

                buffer = ""
                decoder = json.JSONDecoder()

                async for chunk in response.aiter_text():
                    buffer += chunk

                    while True:
                        # Clean up buffer to find start of JSON object
                        # The stream is typically a JSON array: [ {...}, {...} ]
                        # We want to strip leading '[', ',', whitespace
                        buffer = buffer.lstrip().lstrip("[").lstrip(",").lstrip()

                        # If buffer is empty or just has closing bracket, wait for more
                        if not buffer or buffer.startswith("]"):
                            if buffer.startswith("]"):
                                buffer = buffer[1:].lstrip()
                            break

                        try:
                            # Try to decode a single JSON object from the start of the buffer
                            obj, idx = decoder.raw_decode(buffer)

                            # Process the object
                            # Structure: candidates[0].content.parts[0].text
                            candidates = obj.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                if parts:
                                    text = parts[0].get("text", "")
                                    if text:
                                        yield text

                            # Advance buffer past this object
                            buffer = buffer[idx:]

                        except json.JSONDecodeError:
                            # Incomplete JSON object, wait for more data
                            break

    async def generate(
        self,
        system_prompt: str,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        contents = []
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        contents.append({"role": "user", "parts": [{"text": user_input}]})

        model = kwargs.get("model", "gemini-pro")
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        payload = {
            "contents": contents,
            "system_instruction": {"parts": [{"text": system_prompt}]},
            **{k: v for k, v in kwargs.items() if k != "model"},
        }

        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=60.0
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Google API error ({response.status_code}): {response.text}"
                )

            data = response.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                raise RuntimeError(f"Unexpected Google API response: {data}")
