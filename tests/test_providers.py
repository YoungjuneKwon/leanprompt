"""
Unit tests for vLLM and llama-cpp-python provider implementations.
These tests verify that the providers are correctly initialized and configured.
"""

import pytest
from fastapi import FastAPI
from leanprompt import LeanPrompt
from leanprompt.providers.vllm import VLLMProvider
from leanprompt.providers.llama_cpp import LlamaCppProvider
from leanprompt.providers.openai import OpenAIProvider


class TestVLLMProvider:
    """Test suite for VLLMProvider"""

    def test_vllm_provider_initialization_with_api_key(self):
        """Test that VLLMProvider correctly initializes with an API key"""
        provider = VLLMProvider(
            base_url="http://localhost:8000/v1",
            api_key="test-api-key"
        )
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.api_key == "test-api-key"

    def test_vllm_provider_initialization_without_api_key(self):
        """Test that VLLMProvider uses EMPTY as default API key when none provided"""
        provider = VLLMProvider(base_url="http://localhost:8000/v1")
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.api_key == "EMPTY"

    def test_vllm_provider_is_openai_compatible(self):
        """Test that VLLMProvider inherits from OpenAIProvider"""
        provider = VLLMProvider(base_url="http://localhost:8000/v1")
        assert isinstance(provider, OpenAIProvider)

    def test_vllm_provider_in_leanprompt(self):
        """Test that LeanPrompt correctly initializes with vllm provider"""
        app = FastAPI()
        lp = LeanPrompt(
            app,
            provider="vllm",
            base_url="http://localhost:8000/v1",
            api_key="test-key",
            prompt_dir="examples/prompts"
        )
        assert isinstance(lp.provider, VLLMProvider)
        assert lp.provider.base_url == "http://localhost:8000/v1"
        assert lp.provider.api_key == "test-key"

    def test_vllm_provider_in_leanprompt_without_api_key(self):
        """Test that LeanPrompt with vllm works without API key"""
        app = FastAPI()
        lp = LeanPrompt(
            app,
            provider="vllm",
            base_url="http://localhost:8000/v1",
            prompt_dir="examples/prompts"
        )
        assert isinstance(lp.provider, VLLMProvider)
        assert lp.provider.api_key == "EMPTY"

    def test_vllm_provider_requires_base_url(self):
        """Test that LeanPrompt raises error when base_url is missing for vllm"""
        app = FastAPI()
        with pytest.raises(ValueError, match="base_url is required for vLLM provider"):
            LeanPrompt(
                app,
                provider="vllm",
                prompt_dir="examples/prompts"
            )


class TestLlamaCppProvider:
    """Test suite for LlamaCppProvider"""

    def test_llama_cpp_provider_initialization_with_api_key(self):
        """Test that LlamaCppProvider correctly initializes with an API key"""
        provider = LlamaCppProvider(
            base_url="http://localhost:8000/v1",
            api_key="test-api-key"
        )
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.api_key == "test-api-key"

    def test_llama_cpp_provider_initialization_without_api_key(self):
        """Test that LlamaCppProvider uses EMPTY as default API key when none provided"""
        provider = LlamaCppProvider(base_url="http://localhost:8000/v1")
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.api_key == "EMPTY"

    def test_llama_cpp_provider_is_openai_compatible(self):
        """Test that LlamaCppProvider inherits from OpenAIProvider"""
        provider = LlamaCppProvider(base_url="http://localhost:8000/v1")
        assert isinstance(provider, OpenAIProvider)

    def test_llama_cpp_provider_in_leanprompt(self):
        """Test that LeanPrompt correctly initializes with llama-cpp provider"""
        app = FastAPI()
        lp = LeanPrompt(
            app,
            provider="llama-cpp",
            base_url="http://localhost:8000/v1",
            api_key="test-key",
            prompt_dir="examples/prompts"
        )
        assert isinstance(lp.provider, LlamaCppProvider)
        assert lp.provider.base_url == "http://localhost:8000/v1"
        assert lp.provider.api_key == "test-key"

    def test_llama_cpp_provider_in_leanprompt_without_api_key(self):
        """Test that LeanPrompt with llama-cpp works without API key"""
        app = FastAPI()
        lp = LeanPrompt(
            app,
            provider="llama-cpp",
            base_url="http://localhost:8000/v1",
            prompt_dir="examples/prompts"
        )
        assert isinstance(lp.provider, LlamaCppProvider)
        assert lp.provider.api_key == "EMPTY"

    def test_llama_cpp_provider_requires_base_url(self):
        """Test that LeanPrompt raises error when base_url is missing for llama-cpp"""
        app = FastAPI()
        with pytest.raises(ValueError, match="base_url is required for llama-cpp-python provider"):
            LeanPrompt(
                app,
                provider="llama-cpp",
                prompt_dir="examples/prompts"
            )


class TestProviderCompatibility:
    """Test suite for provider compatibility and API behavior"""

    def test_vllm_provider_generate_method_exists(self):
        """Test that VLLMProvider has generate method from OpenAIProvider"""
        provider = VLLMProvider(base_url="http://localhost:8000/v1")
        assert hasattr(provider, 'generate')
        assert callable(provider.generate)

    def test_vllm_provider_generate_stream_method_exists(self):
        """Test that VLLMProvider has generate_stream method from OpenAIProvider"""
        provider = VLLMProvider(base_url="http://localhost:8000/v1")
        assert hasattr(provider, 'generate_stream')
        assert callable(provider.generate_stream)

    def test_llama_cpp_provider_generate_method_exists(self):
        """Test that LlamaCppProvider has generate method from OpenAIProvider"""
        provider = LlamaCppProvider(base_url="http://localhost:8000/v1")
        assert hasattr(provider, 'generate')
        assert callable(provider.generate)

    def test_llama_cpp_provider_generate_stream_method_exists(self):
        """Test that LlamaCppProvider has generate_stream method from OpenAIProvider"""
        provider = LlamaCppProvider(base_url="http://localhost:8000/v1")
        assert hasattr(provider, 'generate_stream')
        assert callable(provider.generate_stream)
