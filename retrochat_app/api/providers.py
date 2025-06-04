from __future__ import annotations

"""Provider handlers for different API formats."""
import json
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple

from retrochat_app.core.config import Configuration


def _merge_params(user_params: Dict[str, Any], provider: dict | None) -> Dict[str, Any]:
    provider_params = provider.get("params", {}) if provider else {}
    return {**provider_params, **user_params}


class BaseProvider:
    """Base class for providers."""

    def __init__(self, config: Configuration, provider_cfg: dict | None) -> None:
        self.config = config
        self.provider_cfg = provider_cfg or {}

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    def build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        headers.update(self.provider_cfg.get("headers", {}))
        return headers

    def endpoint(self) -> str:
        return self.provider_cfg.get(
            "chat_completions_endpoint", self.config.api.chat_completions_endpoint
        )

    # ------------------------------------------------------------------
    # Payload/response
    # ------------------------------------------------------------------
    def build_payload(self, messages: List[Dict[str, Any]], *, stream: bool) -> Dict[str, Any]:
        params = _merge_params(self.config.model.get_api_parameters(), self.provider_cfg)
        payload = {"messages": messages, "stream": stream}
        payload.update(params)
        return payload

    def parse_response(self, data: Dict[str, Any]) -> Optional[str]:
        if data.get("choices") and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            if "delta" in choice and "content" in choice["delta"]:
                return choice["delta"]["content"]
        return None

    def iter_stream(self, lines: Iterable[bytes]) -> Generator[str, None, None]:
        for line in lines:
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                json_content = decoded[len("data: "):]
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
    """Provider handler for Ollama style APIs."""

    def endpoint(self) -> str:  # type: ignore[override]
        return self.provider_cfg.get("chat_completions_endpoint", "http://localhost:11434/api/chat")

    def build_payload(self, messages: List[Dict[str, Any]], *, stream: bool) -> Dict[str, Any]:  # type: ignore[override]
        params = _merge_params(self.config.model.get_api_parameters(), self.provider_cfg)

        system_prompt = params.pop("system_prompt", None)
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {"model": params.get("model"), "messages": messages, "stream": stream}

        format_val = params.pop("format", None)
        if format_val is not None:
            payload["format"] = format_val

        keep_alive = params.pop("keep_alive", None)
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive

        option_keys = [
            "num_keep",
            "seed",
            "max_tokens",
            "top_k",
            "top_p",
            "min_p",
            "typical_p",
            "repeat_last_n",
            "temperature",
            "repeat_penalty",
            "presence_penalty",
            "frequency_penalty",
            "penalize_newline",
            "stop",
            "numa",
            "num_ctx",
            "num_batch",
            "num_gpu",
            "main_gpu",
            "use_mmap",
            "num_thread",
        ]
        options = {}
        for key in option_keys:
            val = params.get(key)
            if val is not None and val != []:
                # rename max_tokens -> num_predict
                if key == "max_tokens":
                    options["num_predict"] = val
                else:
                    options[key] = val

        if options:
            payload["options"] = options
        return payload

    def parse_response(self, data: Dict[str, Any]) -> Optional[str]:  # type: ignore[override]
        msg = data.get("message")
        if isinstance(msg, dict):
            return msg.get("content")
        return None

    def iter_stream(self, lines: Iterable[bytes]) -> Generator[str, None, None]:  # type: ignore[override]
        for line in lines:
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            text = self.parse_response(data)
            if text:
                yield text
            if data.get("done"):
                break


def get_provider_handler(config: Configuration) -> BaseProvider:
    from retrochat_app.core import provider_manager

    cfg = provider_manager.get_active_provider()
    if cfg and cfg.get("type") == "ollama":
        return OllamaProvider(config, cfg)
    return BaseProvider(config, cfg)


