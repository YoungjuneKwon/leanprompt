from setuptools import setup, find_packages

setup(
    name="leanprompt",
    version="0.1.0",
    description="A FastAPI-based LLM integration framework for engineering-centric AI development.",
    author="OpenCode",
    packages=find_packages(),
    install_requires=["fastapi", "uvicorn", "pydantic", "httpx", "pyyaml"],
    python_requires=">=3.8",
)
