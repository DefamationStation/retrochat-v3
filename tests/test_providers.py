"""
Test script for the provider system.
"""

import sys
import os

# Add the project root and src to the Python path
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.core.config_manager import ConfigManager
from src.core.model_manager import ModelManager
from src.core.chat import Chat
from src.providers import provider_factory

def test_provider_system():
    print("=== Testing Provider System ===")
    
    # Test provider factory
    print("\n1. Testing Provider Factory")
    available_providers = provider_factory.get_available_providers()
    print(f"Available providers: {available_providers}")
    
    # Test config manager
    print("\n2. Testing Config Manager")
    config_manager = ConfigManager()
    current_provider = config_manager.get_current_provider()
    print(f"Current provider: {current_provider}")
    
    configured_providers = config_manager.list_configured_providers()
    print(f"Configured providers: {configured_providers}")
    
    # Test model manager
    print("\n3. Testing Model Manager")
    model_manager = ModelManager(config_manager)
    
    provider_name = model_manager.get_current_provider_name()
    print(f"Model manager provider: {provider_name}")
    
    # Test connection
    print("\n4. Testing Provider Connection")
    connection_ok = model_manager.test_current_provider()
    print(f"Connection test: {'✓ Success' if connection_ok else '✗ Failed'}")
    
    if connection_ok:
        # Test model listing
        print("\n5. Testing Model Listing")
        models = model_manager.get_models()
        print(f"Found {len(models)} models")
        if models:
            print(f"First model: {models[0].get('id', 'Unknown')}")
    
    # Test chat initialization
    print("\n6. Testing Chat Initialization")
    chat = Chat(config_manager)
    chat_provider = chat.get_current_provider_name()
    print(f"Chat provider: {chat_provider}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_provider_system()
