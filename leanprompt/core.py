import os
import yaml
import hashlib
from typing import Optional, Type, Callable, Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel, ValidationError
from .providers.deepseek import DeepSeekProvider
from .providers.openai import OpenAIProvider
from .providers.google import GoogleProvider
from .providers.ollama import OllamaProvider
from .providers.base import BaseProvider
from .guard import Guard


class LeanPrompt:
    def __init__(
        self,
        app: FastAPI,
        provider: str = "openai",
        prompt_dir: str = "prompts",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,  # For Ollama or Custom URLs
        on_validation_error: str = "ignore",  # ignore, retry, raise
        max_retries: int = 3,  # 0 = infinite
        **provider_kwargs,
    ):
        self.app = app
        self.prompt_dir = prompt_dir
        self.provider_name = provider
        self.on_validation_error = on_validation_error
        self.max_retries = max_retries

        # Initialize provider
        if provider == "deepseek":
            if not api_key:
                raise ValueError("api_key is required for DeepSeek provider.")
            self.provider = DeepSeekProvider(api_key=api_key, **provider_kwargs)
        elif provider == "openai":
            if not api_key:
                raise ValueError("api_key is required for OpenAI provider.")
            self.provider = OpenAIProvider(api_key=api_key, **provider_kwargs)
        elif provider == "google":
            if not api_key:
                raise ValueError("api_key is required for Google provider.")
            self.provider = GoogleProvider(api_key=api_key, **provider_kwargs)
        elif provider == "ollama":
            # api_key not required for Ollama
            ollama_url = base_url or "http://localhost:11434"
            self.provider = OllamaProvider(base_url=ollama_url, **provider_kwargs)
        elif provider == "vllm":
            if not base_url:
                raise ValueError("base_url is required for vLLM provider.")
            # vLLM is OpenAI-compatible
            self.provider = OpenAIProvider(
                api_key=api_key or "vllm", base_url=base_url, **provider_kwargs
            )
        elif provider == "llama-cpp":
            if not base_url:
                raise ValueError("base_url is required for llama-cpp-python provider.")
            # llama-cpp-python server is OpenAI-compatible
            self.provider = OpenAIProvider(
                api_key=api_key or "llama-cpp", base_url=base_url, **provider_kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.routes_info = {}  # Store path -> prompt_file mapping
        self._setup_websocket()

    def _load_prompt(self, prompt_file: str):
        prompt_path = os.path.join(self.prompt_dir, prompt_file)
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple frontmatter parsing
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return frontmatter, body
        return {}, content.strip()

    def _setup_websocket(self):
        # WebSocket endpoint with Context Caching (Session Memory)
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await websocket.accept()
            # History keyed by path: { "/path1": [...], "/path2": [...] }
            path_history: Dict[str, List[Dict[str, str]]] = {}

            try:
                while True:
                    # Expect JSON input: {"path": "/foo", "message": "hello"}
                    try:
                        data = await websocket.receive_json()
                        path = data.get("path")
                        user_input = data.get("message")

                        if not path or not user_input:
                            await websocket.send_json(
                                {
                                    "error": "Fields 'path' and 'message' are required",
                                    "path": path,
                                }
                            )
                            continue
                    except Exception:
                        await websocket.send_json(
                            {"error": "Invalid JSON format", "path": None}
                        )
                        continue

                    # Lookup prompt file from routes_info
                    prompt_file = self.routes_info.get(path)
                    if not prompt_file:
                        await websocket.send_json(
                            {"error": f"No route found for path: {path}", "path": path}
                        )
                        continue

                    # Load prompt
                    try:
                        config, system_prompt = self._load_prompt(prompt_file)
                    except FileNotFoundError:
                        await websocket.send_json(
                            {
                                "error": f"Prompt file not found: {prompt_file}",
                                "path": path,
                            }
                        )
                        continue

                    # Initialize history for this path if needed
                    if path not in path_history:
                        path_history[path] = []

                    history = path_history[path]

                    # Prepare kwargs from config
                    kwargs = {}
                    if config.get("model"):
                        kwargs["model"] = config["model"]

                    # Generate Response
                    response_buffer = ""
                    # Streaming generation
                    # Since we need to wrap the output in JSON {"response": ...}, streaming strictly chunk-by-chunk
                    # as raw text is tricky if we want to maintain the protocol.
                    # However, typical WS streaming sends partial updates.
                    # The user requested: output: { "response": "..." }
                    # To stream this, we can send multiple JSON frames like { "response": "chunk" }
                    # OR accumulate and send one JSON at the end.
                    # Given "Context Caching" implies interactivity, streaming is preferred.
                    # Let's assume we stream partial chunks wrapped in JSON for now, or just raw text?
                    # The prompt says: output: { "response": "..." }. This usually implies the final response.
                    # But core features emphasize streaming. Let's support both or assume streaming chunks
                    # with a flag, but for compatibility with the request format let's send ONE final JSON
                    # if we want to strictly follow { "response": "..." } as a single message unit.
                    # BUT, usually WS is for streaming. Let's assume we send ONE final message for now
                    # to strictly match the requested format, OR send partials.
                    # Let's send partials as { "response": "chunk", "stream": true } or similar?
                    # The requirement "output: { "response": "..." }" likely means the payload structure.
                    # If we stream, we might send many of these.

                    # For now, let's accumulate and send ONE response to strictly match the requested JSON format example.
                    # If streaming is absolutely required, we can change this.

                    full_response = ""
                    async for chunk in self.provider.generate_stream(
                        system_prompt=system_prompt,
                        user_input=user_input,
                        history=history,
                        **kwargs,
                    ):
                        full_response += chunk
                        # If we want real-time streaming:
                        # await websocket.send_json({"response": chunk, "partial": True})

                    # Send final complete response as requested
                    await websocket.send_json({"response": full_response, "path": path})

                    # Update History (Context Caching)
                    history.append({"role": "user", "content": user_input})
                    history.append({"role": "assistant", "content": full_response})

            except WebSocketDisconnect:
                print(f"Client #{client_id} disconnected")

    def route(
        self,
        path: str,
        prompt_file: Optional[str] = None,
    ):
        def decorator(func: Callable):
            # Resolve prompt file path logic
            resolved_prompt_file = prompt_file
            if not resolved_prompt_file:
                # Remove leading slash if present
                clean_path = path.lstrip("/")
                # Add .md extension if missing
                if not clean_path.endswith(".md"):
                    clean_path += ".md"
                resolved_prompt_file = clean_path

            # Store routing info for WebSocket
            self.routes_info[path] = resolved_prompt_file

            # Helper to load prompt (capture variable)
            def load_current_prompt():
                return self._load_prompt(resolved_prompt_file)

            @self.app.post(path)
            async def wrapper(request: Request):
                # Validate Content-Type
                if request.headers.get("content-type") != "application/json":
                    raise HTTPException(
                        status_code=400, detail="Content-Type must be application/json"
                    )

                # Parse Body
                try:
                    body = await request.json()
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid JSON body")

                user_input = body.get("message")
                if not user_input:
                    raise HTTPException(
                        status_code=400,
                        detail="Field 'message' is required in JSON body",
                    )

                # 1. Load Prompt
                config, system_prompt = load_current_prompt()

                # 2. Setup Loop
                retries = 0
                history: List[Dict[str, str]] = []

                # Check model config
                kwargs = {}
                if config.get("model"):
                    kwargs["model"] = config["model"]

                while True:
                    # 3. Get LLM Response
                    response_text = await self.provider.generate(
                        system_prompt=system_prompt,
                        user_input=user_input if not history else "",
                        history=history,
                        **kwargs,
                    )

                    # 4. Validation (Guard)
                    output_model = getattr(func, "_output_model", None)
                    custom_validator = getattr(func, "_custom_validator", None)

                    validated_data = None
                    validation_error = None

                    try:
                        if output_model:
                            validated_data = Guard.parse_and_validate(
                                response_text, output_model
                            )
                        elif custom_validator:
                            validated_data = custom_validator(response_text)
                        else:
                            # No validation needed
                            return response_text
                    except (ValueError, ValidationError) as e:
                        validation_error = e

                    if not validation_error:
                        return validated_data

                    # Handle Failure
                    if self.on_validation_error == "ignore":
                        return ""

                    if self.on_validation_error == "raise":
                        raise HTTPException(
                            status_code=500,
                            detail=f"LLM Output Validation Failed: {str(validation_error)}",
                        )

                    if self.on_validation_error == "retry":
                        if self.max_retries > 0 and retries >= self.max_retries:
                            return ""

                        if retries == 0:
                            history.append({"role": "user", "content": user_input})
                            history.append(
                                {"role": "assistant", "content": response_text}
                            )
                        else:
                            history.append({"role": "user", "content": user_input})
                            history.append(
                                {"role": "assistant", "content": response_text}
                            )

                        user_input = f"Validation Error: {str(validation_error)}. Please correct your response to match the required schema."
                        retries += 1
                        continue

                return response_text

            return wrapper

        return decorator
