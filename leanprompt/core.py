import os
import yaml
import hashlib
import inspect
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
        api_prefix: str = "",
        ws_path: str = "/ws",
        ws_auth: Optional[Callable[[WebSocket], Any]] = None,
        **provider_kwargs,
    ):
        self.app = app
        self.prompt_dir = prompt_dir
        self.provider_name = provider
        self.on_validation_error = on_validation_error
        self.max_retries = max_retries
        self.api_prefix = self._normalize_prefix(api_prefix)
        self.ws_path = self._initialize_ws_path(ws_path)
        self.ws_auth = ws_auth

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

    @staticmethod
    def _normalize_route_path(path: str) -> str:
        normalized = (path or "").strip()
        if not normalized:
            return "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if normalized != "/":
            normalized = normalized.rstrip("/")
        return normalized

    @classmethod
    def _normalize_prefix(cls, prefix: str) -> str:
        normalized = (prefix or "").strip()
        if not normalized:
            return ""
        normalized = cls._normalize_route_path(normalized)
        return "" if normalized == "/" else normalized

    @classmethod
    def _normalize_ws_path(cls, ws_path: str) -> str:
        normalized = cls._normalize_route_path(ws_path or "/ws")
        return normalized or "/ws"

    def _apply_prefix(self, path: str) -> str:
        normalized = self._normalize_route_path(path)
        if not self.api_prefix:
            return normalized
        if normalized == self.api_prefix or normalized.startswith(f"{self.api_prefix}/"):
            return normalized
        return f"{self.api_prefix}{normalized}"

    def _initialize_ws_path(self, ws_path: str) -> str:
        ws_path_input = ws_path or "/ws"
        is_relative_ws = bool(ws_path_input) and not ws_path_input.startswith("/")
        normalized_ws_path = self._normalize_ws_path(ws_path_input)
        if self.api_prefix and is_relative_ws:
            normalized_ws_path = self._apply_prefix(normalized_ws_path)
        if normalized_ws_path == "/":
            raise ValueError(
                "ws_path cannot be '/' as it would shadow all HTTP routes on the same app. "
                "Use a path like '/ws'."
            )
        return normalized_ws_path

    def _strip_prefix(self, path: str) -> str:
        normalized = self._normalize_route_path(path)
        if not self.api_prefix:
            return normalized
        if normalized == self.api_prefix:
            return "/"
        if normalized.startswith(f"{self.api_prefix}/"):
            return normalized[len(self.api_prefix) :] or "/"
        return normalized

    async def _run_auth_hook(self, auth_hook: Callable[[Any], Any], payload: Any) -> Any:
        result = auth_hook(payload)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _authorize_websocket(self, websocket: WebSocket) -> bool:
        if not self.ws_auth:
            return True
        try:
            result = await self._run_auth_hook(self.ws_auth, websocket)
        except HTTPException:
            await websocket.close(code=1008)
            return False
        if result is False:
            await websocket.close(code=1008)
            return False
        return True

    async def _authorize_request(self, request: Request, func: Callable) -> None:
        auth_validator = getattr(func, "_auth_validator", None)
        if not auth_validator:
            return
        auth_result = await self._run_auth_hook(auth_validator, request)
        if auth_result is False:
            raise HTTPException(status_code=401, detail="Unauthorized")

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
        ws_route = f"{self.ws_path}/{{client_id}}"

        @self.app.websocket(ws_route)
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            if not await self._authorize_websocket(websocket):
                return
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
                    prefixed_path = self._apply_prefix(path)
                    prompt_file = self.routes_info.get(prefixed_path)
                    if not prompt_file:
                        await websocket.send_json(
                            {
                                "error": f"No route found for path: {path}",
                                "path": path,
                            }
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
                    history_key = prefixed_path
                    if history_key not in path_history:
                        path_history[history_key] = []

                    history = path_history[history_key]

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
            normalized_path = self._normalize_route_path(path)
            prompt_path = self._strip_prefix(normalized_path)

            # Resolve prompt file path logic
            resolved_prompt_file = prompt_file
            if not resolved_prompt_file:
                # Remove leading slash if present
                clean_path = prompt_path.lstrip("/")
                # Add .md extension if missing
                if not clean_path.endswith(".md"):
                    clean_path += ".md"
                resolved_prompt_file = clean_path

            prefixed_path = self._apply_prefix(normalized_path)

            # Store routing info for WebSocket
            self.routes_info[prefixed_path] = resolved_prompt_file

            # Helper to load prompt (capture variable)
            def load_current_prompt():
                return self._load_prompt(resolved_prompt_file)

            @self.app.post(prefixed_path)
            async def wrapper(request: Request):
                await self._authorize_request(request, func)
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
