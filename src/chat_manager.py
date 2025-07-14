"""
Chat manager for handling conversations
"""
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .providers import ChatProvider, ChatMessage, ChatResponse
from .providers.factory import get_provider


@dataclass
class Conversation:
    """Represents a chat conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Chat"
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation"""
        message = ChatMessage(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Auto-generate title from first user message
        if role == "user" and self.title == "New Chat" and len(self.messages) <= 2:
            # Create title from first 50 characters of user message
            title = content.strip()[:50]
            if len(title) < len(content.strip()):
                title += "..."
            self.title = title
    
    def get_context_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get messages for context, optionally limited to recent messages"""
        if limit is None:
            return self.messages.copy()
        
        # Keep system messages + last N messages
        system_messages = [msg for msg in self.messages if msg.role == "system"]
        other_messages = [msg for msg in self.messages if msg.role != "system"]
        
        if limit <= 0:
            return system_messages
        
        return system_messages + other_messages[-limit:]


class ChatManager:
    """Manages chat conversations and provider interactions"""
    
    def __init__(self, provider_name: str, provider_config: Dict[str, Any], chat_config: Dict[str, Any]):
        self.provider_name = provider_name
        self.provider_config = provider_config
        self.chat_config = chat_config
        self._provider: Optional[ChatProvider] = None
        self._current_conversation: Optional[Conversation] = None
        
    def _get_provider(self) -> ChatProvider:
        """Get or create the chat provider"""
        if self._provider is None:
            self._provider = get_provider(self.provider_name, self.provider_config)
        return self._provider
    
    def start_new_conversation(self, system_prompt: Optional[str] = None) -> Conversation:
        """Start a new conversation"""
        conversation = Conversation()
        
        # Add system prompt if provided
        if system_prompt:
            conversation.add_message("system", system_prompt)
        elif self.chat_config.get("system_prompt"):
            conversation.add_message("system", self.chat_config["system_prompt"])
        
        self._current_conversation = conversation
        return conversation
    
    def get_current_conversation(self) -> Optional[Conversation]:
        """Get the current conversation"""
        return self._current_conversation
    
    def set_conversation(self, conversation: Conversation):
        """Set the current conversation"""
        self._current_conversation = conversation
    
    def send_message(self, content: str, stream: Optional[bool] = None) -> ChatResponse:
        """Send a message and get response"""
        if self._current_conversation is None:
            self.start_new_conversation()
        
        conversation = self._current_conversation
        assert conversation is not None  # Help type checker
        
        # Add user message
        conversation.add_message("user", content)
        
        # Get context messages
        context_messages = conversation.get_context_messages()
        
        # Prepare generation parameters from chat config
        kwargs = {
            "max_tokens": self.chat_config.get("max_tokens", 8000),
            "temperature": self.chat_config.get("temperature", 0.7),
            "top_p": self.chat_config.get("top_p", 1.0),
            "top_k": self.chat_config.get("top_k", 40),
            "frequency_penalty": self.chat_config.get("frequency_penalty", 0.0),
            "presence_penalty": self.chat_config.get("presence_penalty", 0.0),
            "repeat_penalty": self.chat_config.get("repeat_penalty", 1.1),
            "seed": self.chat_config.get("seed"),
            "stop_sequences": self.chat_config.get("stop_sequences"),
        }
        
        # Get provider and send request
        provider = self._get_provider()
        
        if stream is None:
            stream = self.chat_config.get("stream", True)
        
        if stream:
            # For streaming, we need to collect the response differently
            content_parts = []
            for chunk in provider.chat_stream(context_messages, **kwargs):
                content_parts.append(chunk)
            
            full_content = "".join(content_parts)
            conversation.add_message("assistant", full_content)
            return ChatResponse(content=full_content)
        else:
            response = provider.chat(context_messages, **kwargs)
            # Add assistant response to conversation
            conversation.add_message("assistant", response.content)
            return response
    
    def send_message_stream(self, content: str) -> Iterator[str]:
        """Send a message and get streaming response"""
        if self._current_conversation is None:
            self.start_new_conversation()
        
        conversation = self._current_conversation
        assert conversation is not None  # Help type checker
        
        # Add user message
        conversation.add_message("user", content)
        
        # Get context messages
        context_messages = conversation.get_context_messages()
        
        # Prepare generation parameters from chat config
        kwargs = {
            "max_tokens": self.chat_config.get("max_tokens", 8000),
            "temperature": self.chat_config.get("temperature", 0.7),
            "top_p": self.chat_config.get("top_p", 1.0),
            "top_k": self.chat_config.get("top_k", 40),
            "frequency_penalty": self.chat_config.get("frequency_penalty", 0.0),
            "presence_penalty": self.chat_config.get("presence_penalty", 0.0),
            "repeat_penalty": self.chat_config.get("repeat_penalty", 1.1),
            "seed": self.chat_config.get("seed"),
            "stop_sequences": self.chat_config.get("stop_sequences"),
        }
        
        # Get provider and send request
        provider = self._get_provider()
        
        content_parts = []
        for chunk_response in provider.chat_stream(context_messages, **kwargs):
            # Extract content from ChatResponse object
            chunk_content = getattr(chunk_response, 'content', str(chunk_response))
            content_parts.append(chunk_content)
            yield chunk_content
        
        # Add complete response to conversation
        full_content = "".join(content_parts)
        conversation.add_message("assistant", full_content)
    
    def list_models(self) -> List[str]:
        """List available models from the provider"""
        provider = self._get_provider()
        return provider.list_models()
    
    def set_model(self, model: str):
        """Set the model to use"""
        provider = self._get_provider()
        provider.set_model(model)
    
    def get_model(self) -> Optional[str]:
        """Get the current model"""
        provider = self._get_provider()
        return provider.get_model()
    
    def is_provider_available(self) -> bool:
        """Check if the provider is available"""
        try:
            provider = self._get_provider()
            return provider.is_available()
        except Exception:
            return False
