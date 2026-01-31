from fastapi import FastAPI, Request, WebSocket
from leanprompt import LeanPrompt, Guard
from pydantic import BaseModel
import uvicorn
import os


# Define output models
class MoodJson(BaseModel):
    current_mood: str
    confidence: float
    reason: str


class CalculationResult(BaseModel):
    result: int


app = FastAPI()

# Initialize LeanPrompt
# Parse env var: LEANPROMPT_LLM_PROVIDER=openai|api_key
# Default to openai|dummy_key if not set, though connection will fail without real key
provider_env = os.getenv("LEANPROMPT_LLM_PROVIDER", "openai|dummy_key")
provider_name, api_key = provider_env.split("|", 1)

api_prefix = os.getenv("LEANPROMPT_API_PREFIX", "")
ws_path = os.getenv("LEANPROMPT_WS_PATH", "/ws")


def _extract_auth_header(payload: Request | WebSocket) -> str:
    return payload.headers.get("authorization", "")


def require_jwt(payload: Request | WebSocket) -> bool:
    # NOTE: Example only. Insecure for production. Validate JWT signature, expiry, and claims.
    # Example: jwt.decode(token, key, algorithms=["HS256"])
    return bool(_extract_auth_header(payload))


lp = LeanPrompt(
    app,
    provider=provider_name,
    prompt_dir="examples/prompts",
    api_key=api_key,
    api_prefix=api_prefix,
    ws_path=ws_path,
    ws_auth=require_jwt,
)


@lp.route("/calc/add", prompt_file="add.md")
@Guard.validate(CalculationResult)
async def add(user_input: str):
    """
    Performs addition based on user input.
    """
    pass


@lp.route("/calc/multiply", prompt_file="multiply.md")
@Guard.validate(CalculationResult)
async def multiply(user_input: str):
    """
    Performs multiplication based on user input.
    """
    pass


@lp.route("/secure/add", prompt_file="add.md")
@Guard.auth(require_jwt)
@Guard.validate(CalculationResult)
async def secure_add(user_input: str):
    """
    Performs addition but requires a JWT in the Authorization header.
    """
    pass


@lp.route("/mood/json", prompt_file="mood_json.md")
@Guard.validate(MoodJson)
async def get_mood_json(user_input: str):
    """
    Returns the mood analysis in JSON format based on the user's input.
    """
    pass  # The decorator handles the logic


@lp.route("/mood/yaml", prompt_file="mood_yaml.md")
# @Guard.validate(MoodYaml) # Removed as model def was removed
async def get_mood_yaml(user_input: str):
    """
    Returns the mood analysis in YAML format based on the user's input.
    """
    pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
