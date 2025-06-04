import os
import sys
import json
import importlib

import pytest

# Ensure project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_add_provider_base_with_v1(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Reload modules so APP_CONFIG_DIR picks up the temp path
    import retrochat_app.core.config_manager as config_manager
    importlib.reload(config_manager)
    import retrochat_app.core.provider_manager as provider_manager
    importlib.reload(provider_manager)

    # Prevent editor from opening
    monkeypatch.setattr(provider_manager, "_launch_editor", lambda path: None)

    success, file_path = provider_manager.add_provider(
        name="OpenRouterTest",
        type="openai",
        api_base_url="https://openrouter.ai/api/v1"
    )
    assert success
    with open(file_path, "r") as f:
        cfg = json.load(f)
    assert cfg["chat_completions_endpoint"] == "https://openrouter.ai/api/v1/chat/completions"

