import os
import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from leanprompt import LeanPrompt, Guard
from leanprompt.providers.deepseek import DeepSeekProvider

# --- Models ---


class CalculationResult(BaseModel):
    result: int


# --- App Factory ---


def create_app():
    app = FastAPI()

    # Parse env var: LEANPROMPT_LLM_PROVIDER=openai|api_key
    # Use dummy default for tests if not set, to allow TestClient instantiation
    # (Actual tests verify env var presence if needed)
    provider_env = os.getenv("LEANPROMPT_LLM_PROVIDER", "openai|dummy_key")
    provider_name, api_key = provider_env.split("|")

    lp = LeanPrompt(
        app, provider=provider_name, prompt_dir="examples/prompts", api_key=api_key
    )

    @lp.route("/add", prompt_file="add.md")
    @Guard.validate(CalculationResult)
    async def add(user_input: str):
        pass

    @lp.route("/multiply", prompt_file="multiply.md")
    @Guard.validate(CalculationResult)
    async def multiply(user_input: str):
        pass

    @lp.route("/add_implicit")
    async def add_implicit(user_input: str):
        pass

    # Validator logic (kept for reference or if we add HTTP test back)
    def validate_markdown_content(text: str):
        if "##" not in text and "**" not in text:
            raise ValueError("Response does not look like Markdown")
        if "Meanings" not in text:
            raise ValueError("Missing required section: 'Meanings'")
        return {"raw_markdown": text}

    # HTTP route for markdown (still valid to have in app)
    @lp.route("/test_markdown", prompt_file="word_relationships.md")
    @Guard.custom(validate_markdown_content)
    async def endpoint(user_input: str):
        pass

    return app


# --- Integration Tests (Client) ---
# ... (previous imports)
from leanprompt.providers.openai import OpenAIProvider

# ... (CalculationResult model)

# ... (create_app logic remains mostly same, ensuring provider is mocked later)


# ... (previous imports)

# ... (CalculationResult model)

# ... (create_app logic remains mostly same, ensuring provider is mocked later)


@pytest.mark.asyncio
async def test_websocket_routing_and_context():
    """Verify WebSocket routing based on 'path' and separate context chains per path"""

    # Run against REAL provider (env var sourced from .bashrc)
    # The tests assume the LLM will respond somewhat deterministically based on the prompt instructions.

    # Ensure LEANPROMPT_LLM_PROVIDER is set
    provider_env = os.getenv("LEANPROMPT_LLM_PROVIDER")
    if not provider_env:
        pytest.skip("LEANPROMPT_LLM_PROVIDER not set in environment")

    app = create_app()
    client = TestClient(app)

    with client.websocket_connect("/ws/test_client") as websocket:
        # 1. Request to /add path (Add Prompt)
        # Expected behavior: The LLM should follow add.md instructions (Calculator, JSON output)
        req_add = {"path": "/add", "message": "10 + 20"}
        websocket.send_json(req_add)
        resp_add = websocket.receive_json()
        print(f"\n[WS Add] {resp_add}")

        # Validation: Check if response contains correct sum in JSON format
        # Note: Response is string inside "response" key.
        # Example: {"response": '{"result": 30}', "path": "/add"}
        assert "30" in resp_add["response"]
        assert resp_add["path"] == "/add"

        # 2. Request to /multiply path (Multiply Prompt)
        req_mult = {"path": "/multiply", "message": "5 * 5"}
        websocket.send_json(req_mult)
        resp_mult = websocket.receive_json()
        print(f"[WS Mult] {resp_mult}")
        assert "25" in resp_mult["response"]
        assert resp_mult["path"] == "/multiply"

        # 3. Context Chaining Test on /test_markdown
        # Prompt: word_relationships.md (Linguist, user provides 3 words, explains meaning/relationship)
        # Turn 1
        req_chat1 = {"path": "/test_markdown", "message": "apple, banana, cherry"}
        websocket.send_json(req_chat1)
        resp_chat1 = websocket.receive_json()
        print(f"[WS Chat 1] {resp_chat1}")
        assert resp_chat1["path"] == "/test_markdown"

        # Turn 2 (Follow-up)
        # We ask something referring to previous context, e.g., "What color are they?"
        req_chat2 = {"path": "/test_markdown", "message": "What color are they?"}
        websocket.send_json(req_chat2)
        resp_chat2 = websocket.receive_json()
        print(f"[WS Chat 2] {resp_chat2}")
        assert resp_chat2["path"] == "/test_markdown"

        # Validation: The response should mention Red/Yellow/etc. proving it remembers "apple, banana, cherry"
        # Simple keyword check
        response_text = resp_chat2["response"].lower()
        assert "red" in response_text or "yellow" in response_text
