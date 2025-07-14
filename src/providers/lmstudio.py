"""
LM Studio provider implementation using OpenAI-compatible API
"""
import time
from typing import List, Dict, Any, Optional, Iterator
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import httpx

from . import ChatProvider, ChatMessage, ChatResponse


class LMStudioProvider(ChatProvider):
    """LM Studio chat provider using OpenAI-compatible endpoints"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None
        self._models_cache = None
        self._models_cache_time = 0
        self._cache_ttl = 60  # Cache models for 60 seconds
        
        # Build base URL
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 1234)
        base_url = self.config.get('base_url')
        
        if base_url:
            self.base_url = base_url.rstrip('/')
        else:
            # Handle IPv4 addresses properly
            if ':' in host and not host.startswith('['):
                # Likely an IPv4 address with port already included
                self.base_url = f"http://{host}"
            else:
                self.base_url = f"http://{host}:{port}"
        
        # Ensure /v1 suffix for OpenAI compatibility
        if not self.base_url.endswith('/v1'):
            self.base_url += '/v1'
    
    def _get_client(self):
        """Get or create OpenAI client configured for LM Studio"""
        if self._client is None:
            if not HAS_OPENAI:
                raise ImportError("OpenAI library is required. Install with: pip install openai")
            
            try:
                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.config.get('api_key', 'lm-studio'),  # LM Studio doesn't require real API key
                    timeout=self.config.get('timeout', 30)
                )
            except Exception as e:
                raise ConnectionError(f"Failed to create OpenAI client for LM Studio at {self.base_url}: {e}")
        
        return self._client
    
    def list_models(self) -> List[str]:
        """List available models from LM Studio /v1/models endpoint"""
        # Check cache first
        now = time.time()
        if (self._models_cache is not None and 
            now - self._models_cache_time < self._cache_ttl):
            return self._models_cache
        
        try:
            # Use direct HTTP request to avoid OpenAI client issues
            models_url = self.base_url + '/models'
            
            with httpx.Client(timeout=self.config.get('timeout', 30)) as client:
                response = client.get(models_url)
                response.raise_for_status()
                
                models_data = response.json()
                model_names = [model['id'] for model in models_data.get('data', [])]
                
                # Update cache
                self._models_cache = model_names
                self._models_cache_time = now
                
                return model_names
                
        except Exception as e:
            print(f"Warning: Could not list models from LM Studio at {models_url}: {e}")
            return []
    
    def _convert_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Convert our message format to OpenAI format"""
        openai_messages = []
        
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return openai_messages
    
    def _is_reasoning_model(self, model_id: str) -> bool:
        """Check if the model is a reasoning model that uses <think> tags"""
        reasoning_keywords = ['r1', 'reasoning', 'deepseek-r1', 'qwq', 'think']
        model_lower = model_id.lower()
        return any(keyword in model_lower for keyword in reasoning_keywords)
    
    def _prepare_reasoning_messages(self, messages: List[Dict[str, str]], model_id: str) -> List[Dict[str, str]]:
        """Prepare messages for reasoning models following DeepSeek-R1 recommendations"""
        if not self._is_reasoning_model(model_id):
            return messages
        
        # For reasoning models, we need to ensure they start thinking
        # Find the last user message and potentially modify it
        prepared_messages = messages.copy()
        
        for i in range(len(prepared_messages) - 1, -1, -1):
            if prepared_messages[i]['role'] == 'user':
                # Add instruction to start with thinking for math problems
                content = prepared_messages[i]['content']
                if any(keyword in content.lower() for keyword in ['math', 'calculate', 'solve', 'problem', 'equation']):
                    if 'reason step by step' not in content.lower():
                        prepared_messages[i]['content'] = content + "\n\nPlease reason step by step, and put your final answer within \\boxed{}."
                break
        
        return prepared_messages
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Send chat request to LM Studio using OpenAI-compatible endpoint"""
        try:
            client = self._get_client()
            
            # Get model
            model_id = self._model or self._get_default_model()
            if not model_id:
                raise ValueError("No model specified and no models available")
            
            # Convert messages
            openai_messages = self._convert_messages(messages)
            
            # Prepare messages for reasoning models
            openai_messages = self._prepare_reasoning_messages(openai_messages, model_id)
            
            # Prepare chat completion parameters (only OpenAI-compatible ones)
            chat_params = {
                "model": model_id,
                "messages": openai_messages,
                "max_tokens": kwargs.get('max_tokens', 8000),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 1.0),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
                "presence_penalty": kwargs.get('presence_penalty', 0.0),
                "stream": False
            }
            
            # Add optional parameters if provided (LM Studio specific ones)
            if 'seed' in kwargs and kwargs['seed'] is not None:
                chat_params['seed'] = kwargs['seed']
            if 'stop_sequences' in kwargs and kwargs['stop_sequences']:
                chat_params['stop'] = kwargs['stop_sequences']
            
            # Get response
            response = client.chat.completions.create(**chat_params)
            
            # Extract content
            content = response.choices[0].message.content if response.choices else ""
            finish_reason = response.choices[0].finish_reason if response.choices else "unknown"
            
            return ChatResponse(
                content=content,
                model=model_id,
                finish_reason=finish_reason
            )
                
        except Exception as e:
            raise RuntimeError(f"LM Studio chat error: {e}")
    
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[ChatResponse]:
        """Send streaming chat request to LM Studio"""
        try:
            client = self._get_client()
            
            # Get model
            model_id = self._model or self._get_default_model()
            if not model_id:
                raise ValueError("No model specified and no models available")
            
            # Convert messages
            openai_messages = self._convert_messages(messages)
            
            # Prepare messages for reasoning models
            openai_messages = self._prepare_reasoning_messages(openai_messages, model_id)
            
            # Prepare chat completion parameters (only OpenAI-compatible ones)
            chat_params = {
                "model": model_id,
                "messages": openai_messages,
                "max_tokens": kwargs.get('max_tokens', 8000),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 1.0),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
                "presence_penalty": kwargs.get('presence_penalty', 0.0),
                "stream": True
            }
            
            # Add optional parameters if provided (LM Studio specific ones)
            if 'seed' in kwargs and kwargs['seed'] is not None:
                chat_params['seed'] = kwargs['seed']
            if 'stop_sequences' in kwargs and kwargs['stop_sequences']:
                chat_params['stop'] = kwargs['stop_sequences']
            
            # Get streaming response
            response_stream = client.chat.completions.create(**chat_params)
            
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield ChatResponse(
                        content=chunk.choices[0].delta.content,
                        model=model_id,
                        finish_reason=chunk.choices[0].finish_reason or "streaming"
                    )
                    
        except Exception as e:
            raise RuntimeError(f"LM Studio streaming error: {e}")
    
    def is_available(self) -> bool:
        """Check if LM Studio is available by trying to list models"""
        try:
            models = self.list_models()
            return len(models) > 0
        except Exception:
            return False
    
    def _get_default_model(self) -> Optional[str]:
        """Get the first available model if no model is set"""
        models = self.list_models()
        return models[0] if models else None
