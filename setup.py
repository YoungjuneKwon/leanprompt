from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="leanprompt",
    version="0.1.1",
    author="yjkwon_wm2m",
    author_email="yjkwon_wm2m@example.com",
    description="A FastAPI-based LLM integration framework for engineering-centric AI development.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yjkwon_wm2m/leanprompt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    install_requires=["fastapi", "uvicorn", "pydantic", "httpx", "pyyaml", "jinja2"],
    python_requires=">=3.8",
)
