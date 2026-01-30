import functools
from typing import Type, Any, Callable
from pydantic import BaseModel, ValidationError


class Guard:
    @staticmethod
    def pydantic(model: Type[BaseModel]):
        """Returns a validator function that parses JSON into a Pydantic model."""

        def validator(content: str) -> BaseModel:
            return Guard.parse_and_validate(content, model)

        return validator

    @staticmethod
    def json():
        """Returns a validator function that ensures the output is valid JSON."""
        import json

        def validator(content: str) -> Any:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")

        return validator

    @staticmethod
    def validate(model: Type[BaseModel]):
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                func._output_model = model
                return await func(*args, **kwargs)

            wrapper._output_model = model
            return wrapper

        return decorator

    @staticmethod
    def custom(validator_func: Callable[[str], Any]):
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                func._custom_validator = validator_func
                return await func(*args, **kwargs)

            wrapper._custom_validator = validator_func
            return wrapper

        return decorator

    @staticmethod
    def parse_and_validate(content: str, model: Type[BaseModel]) -> BaseModel:
        # Simply delegate to Pydantic's built-in parsing.
        # This assumes the content is a valid JSON string matching the model.
        # We do NOT attempt to strip markdown or parse YAML here.
        try:
            # Try Pydantic v2 API first, fallback to v1
            if hasattr(model, "model_validate_json"):
                return model.model_validate_json(content)
            else:
                return model.parse_raw(content)
        except (ValidationError, ValueError) as e:
            raise ValueError(
                f"Failed to validate LLM output against {model.__name__}: {str(e)}"
            )
