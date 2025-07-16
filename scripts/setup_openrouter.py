#!/usr/bin/env python3
"""
OpenRouter Setup Helper

This script helps you configure OpenRouter as a provider for RetroChat.
"""

import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.config_manager import ConfigManager

def setup_openrouter():
    print("=== OpenRouter Setup Helper ===")
    print()
    
    config_manager = ConfigManager()
    
    # Check if OpenRouter is already configured
    if 'openrouter' in config_manager.list_configured_providers():
        print("OpenRouter is already configured!")
        current_config = config_manager.get_provider_config('openrouter')
        print("Current configuration:")
        for key, value in current_config.items():
            if 'key' in key.lower():
                display_value = f"{value[:8]}..." if value else "not set"
            else:
                display_value = value
            print(f"  {key}: {display_value}")
        
        print()
        overwrite = input("Do you want to reconfigure? (y/N): ").lower()
        if overwrite != 'y':
            return
    
    print("To get started with OpenRouter:")
    print("1. Visit https://openrouter.ai")
    print("2. Sign up for an account")
    print("3. Go to your dashboard and get your API key")
    print("4. Your API key should start with 'sk-or-v1-'")
    print()
    
    api_key = input("Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("API key is required. Setup cancelled.")
        return
    
    if not api_key.startswith('sk-'):
        print("Warning: OpenRouter API keys typically start with 'sk-'")
        continue_anyway = input("Continue anyway? (y/N): ").lower()
        if continue_anyway != 'y':
            return
    
    # Optional configurations
    print()
    print("Optional configurations (press Enter to skip):")
    
    default_model = input("Default model (e.g., openai/gpt-4o): ").strip()
    if not default_model:
        default_model = "openai/gpt-4o"
    
    site_name = input("Site name for OpenRouter leaderboards: ").strip()
    site_url = input("Site URL for OpenRouter leaderboards: ").strip()
    
    stream = input("Enable streaming responses? (Y/n): ").strip().lower()
    stream_enabled = stream != 'n'
    
    system_prompt = input("System prompt (press Enter for default): ").strip()
    if not system_prompt:
        system_prompt = "You're an intelligent AI assistant."
    
    # Build configuration
    openrouter_config = {
        "api_key": api_key,
        "default_model": default_model,
        "stream": stream_enabled,
        "system_prompt": system_prompt
    }
    
    if site_name:
        openrouter_config["site_name"] = site_name
    if site_url:
        openrouter_config["site_url"] = site_url
    
    # Save configuration
    config_manager.set_provider_config('openrouter', openrouter_config)
    
    print()
    print("✓ OpenRouter configuration saved!")
    
    # Test connection
    print("Testing connection...")
    from src.providers import provider_factory
    
    provider = provider_factory.create_provider('openrouter', openrouter_config)
    if provider and provider.test_connection():
        print("✓ Connection test successful!")
        
        # Offer to switch to OpenRouter
        switch = input("Switch to OpenRouter as current provider? (Y/n): ").strip().lower()
        if switch != 'n':
            config_manager.set_current_provider('openrouter')
            print("✓ Switched to OpenRouter as current provider")
        
        # Show some available models
        print("\nFetching available models...")
        try:
            model_manager = provider.create_model_manager()
            models = model_manager.get_models()
            if models:
                print(f"Found {len(models)} available models. First 10:")
                for i, model in enumerate(models[:10]):
                    print(f"  {model.get('id', 'Unknown')}")
            else:
                print("No models found (this might be normal)")
        except Exception as e:
            print(f"Could not fetch models: {e}")
        
    else:
        print("✗ Connection test failed. Please check your API key.")
    
    print()
    print("Setup complete! You can now use the following commands:")
    print("  /provider switch openrouter")
    print("  /model list")
    print("  /provider test")

if __name__ == "__main__":
    setup_openrouter()
