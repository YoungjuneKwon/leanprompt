from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Optional


class BaseProvider(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        yield

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        pass
