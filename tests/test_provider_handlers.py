import os
import sys
import importlib

# Ensure project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrochat_app.api.providers import get_provider_handler, BaseProvider, OllamaProvider
from retrochat_app.core.config import get_config


def test_get_provider_handler_openai():
    cfg = {"type": "openai"}
    provider = get_provider_handler(cfg, get_config())
    assert isinstance(provider, BaseProvider)


def test_get_provider_handler_ollama():
    cfg = {"type": "ollama"}
    provider = get_provider_handler(cfg, get_config())
    assert isinstance(provider, OllamaProvider)
