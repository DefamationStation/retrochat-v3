"""
Abstract base classes for chat providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Response from a chat provider"""
    content: str
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class ChatProvider(ABC):
    """Abstract base class for all chat providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration"""
        self.config = config
        self._model = config.get('model')
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Send a chat request and get response"""
        pass
    
    @abstractmethod
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """Send a chat request and get streaming response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready"""
        pass
    
    @property
    def name(self) -> str:
        """Get provider name"""
        return self.__class__.__name__.lower().replace('provider', '')
    
    def get_model(self) -> Optional[str]:
        """Get the current model"""
        return self._model
    
    def set_model(self, model: str) -> None:
        """Set the current model"""
        self._model = model
