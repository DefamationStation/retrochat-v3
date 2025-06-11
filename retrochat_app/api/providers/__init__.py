"""Provider abstraction layer for LLMClient."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Type
import json


class BaseProvider:
    """Base class for API providers."""

    def __init__(self, cfg: Optional[Dict[str, Any]], config):
        self.cfg = cfg or {}
        self.config = config

    # ----- configuration helpers -----
    def build_endpoint(self) -> str:
        return self.cfg.get("chat_completions_endpoint") or self.config.api.chat_completions_endpoint

    def build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        headers.update(self.cfg.get("headers", {}))
        return headers

    # ----- payload/build helpers -----
    def build_payload(self, messages: list[Dict[str, Any]], params: Dict[str, Any], *, stream: bool) -> Dict[str, Any]:
        payload = dict(params)
        payload["messages"] = messages
        payload["stream"] = stream
        return payload

    # ----- response parsing -----
    def parse_response(self, data: Dict[str, Any]) -> Optional[str]:
        choices = data.get("choices")
        if choices:
            choice = choices[0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            if "delta" in choice and "content" in choice["delta"]:
                return choice["delta"]["content"]
        return None

    def iter_stream(self, response) -> Iterable[str]:
        for line in response.iter_lines():
            if not line:
                continue
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data: "):
                json_content = decoded_line[len("data: ") :]
                if json_content.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(json_content)
                except json.JSONDecodeError:
                    continue
                text = self.parse_response(data)
                if text:
                    yield text


class OllamaProvider(BaseProvider):
    """Provider implementation for Ollama REST API."""

    def build_endpoint(self) -> str:
        return self.cfg.get("chat_completions_endpoint") or "http://localhost:11434/api/generate"

    def build_payload(self, messages: list[Dict[str, Any]], params: Dict[str, Any], *, stream: bool) -> Dict[str, Any]:
        params = dict(params)
        system_prompt = params.pop("system_prompt", None)
        parts: list[str] = []
        if system_prompt:
            parts.append(system_prompt)
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role and content:
                parts.append(f"{role.capitalize()}: {content}")
        prompt = "\n".join(parts)

        options_map = {
            "temperature": params.get("temperature"),
            "top_p": params.get("top_p"),
            "presence_penalty": params.get("presence_penalty"),
            "frequency_penalty": params.get("frequency_penalty"),
            "num_predict": params.get("max_tokens"),
            "stop": params.get("stop_sequences"),
        }
        options = {k: v for k, v in options_map.items() if v is not None and v != []}

        payload = {
            "model": params.get("model"),
            "prompt": prompt,
            "stream": stream,
        }
        if options:
            payload["options"] = options
        return payload

    def parse_response(self, data: Dict[str, Any]) -> Optional[str]:
        return data.get("response")

    def iter_stream(self, response) -> Iterable[str]:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            text = data.get("response")
            if text:
                yield text
            if data.get("done"):
                break


PROVIDER_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "openai": BaseProvider,
    "ollama": OllamaProvider,
}


def get_provider_handler(cfg: Optional[Dict[str, Any]], config) -> BaseProvider:
    provider_type = (cfg or {}).get("type", "openai").lower()
    cls = PROVIDER_REGISTRY.get(provider_type, BaseProvider)
    return cls(cfg, config)


def register_provider(provider_type: str, cls: Type[BaseProvider]) -> None:
    PROVIDER_REGISTRY[provider_type.lower()] = cls
