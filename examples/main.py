from fastapi import FastAPI
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
# Note: Ensure LEANPROMPT_LLM_KEY is set in environment variables
api_key = os.getenv("LEANPROMPT_LLM_KEY")
lp = LeanPrompt(app, provider="openai", prompt_dir="examples/prompts", api_key=api_key)


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
