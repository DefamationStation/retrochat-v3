# RetroChat v3 - Multi-Provider AI Chat Application

A modular chat application that supports multiple AI providers through a unified interface.

## Installation

### Option 1: Standalone Executable (Windows)
Download the latest `rchat.exe` from the [releases page](https://github.com/DefamationStation/retrochat-v3/releases) and run it directly. No Python installation required.

### Option 2: Install via pip
```bash
pip install retrochat-cli
rchat
```

### Option 3: Install from GitHub
```bash
pip install git+https://github.com/DefamationStation/retrochat-v3.git
rchat
```

### Option 4: Development Installation
```bash
git clone https://github.com/DefamationStation/retrochat-v3.git
cd retrochat-v3
pip install -r requirements.txt
python main.py
```

## Features

- **Multi-Provider Support**: Easily switch between different AI providers
- **Automatic Provider Discovery**: New providers are automatically detected
- **Backward Compatibility**: Existing configurations are automatically migrated
- **Streaming Support**: Real-time response streaming
- **Chat Management**: Save, load, and manage conversation history
- **Extensible Architecture**: Easy to add new providers

## Supported Providers

### LM Studio
Local AI model hosting with OpenAI-compatible API.

**Required Configuration:**
- `api_base`: LM Studio server URL (e.g., "http://localhost:1234/v1")
- `api_key`: API key (typically "lm-studio")

### OpenRouter
Access to hundreds of models through a unified API.

**Required Configuration:**
- `api_key`: Your OpenRouter API key (starts with "sk-")

**Optional Configuration:**
- `site_url`: Your site URL for OpenRouter leaderboards
- `site_name`: Your site name for OpenRouter leaderboards

## Configuration

The application uses a `config.json` file with the following structure:

```json
{
  "current_provider": "lmstudio",
  "providers": {
    "lmstudio": {
      "api_base": "http://localhost:1234/v1",
      "api_key": "lm-studio",
      "default_model": "your-model-name",
      "stream": true,
      "system_prompt": "You're an intelligent AI assistant."
    },
    "openrouter": {
      "api_key": "sk-or-v1-your-api-key-here",
      "default_model": "openai/gpt-4o",
      "stream": true,
      "system_prompt": "You're an intelligent AI assistant.",
      "site_url": "https://your-site.com",
      "site_name": "Your App Name"
    }
  }
}
```

## Commands

### Model Management
- `/model list` - List and select available AI models

### Provider Management
- `/provider list` - List all available and configured providers
- `/provider switch <name>` - Switch to a different provider
- `/provider test` - Test connection to current provider
- `/provider config <name>` - Show configuration for a provider

### Settings
- `/set stream true/false` - Enable or disable streaming responses
- `/set system <prompt>` - Set the system prompt for the AI

### Chat Management
- `/chat new` - Start a new chat session
- `/chat save <name>` - Save the current chat with a given name
- `/chat load <name>` - Load a previously saved chat
- `/chat delete <name>` - Delete a saved chat
- `/chat reset` - Clear the current chat's conversation history
- `/chat list` - List all saved chats

### General
- `/help` - Show all available commands
- `/exit` - Exit the application

## Setup

### Prerequisites
```bash
pip install -r requirements.txt
```

### For LM Studio
1. Download and install LM Studio
2. Load a model in LM Studio
3. Start the server (default: http://localhost:1234)
4. Run the application - it will auto-configure for LM Studio

### For OpenRouter
1. Sign up at https://openrouter.ai
2. Get your API key from the dashboard
3. Add OpenRouter configuration to your config.json:

```json
{
  "current_provider": "openrouter",
  "providers": {
    "openrouter": {
      "api_key": "sk-or-v1-your-api-key-here",
      "default_model": "openai/gpt-4o",
      "stream": true,
      "system_prompt": "You're an intelligent AI assistant."
    }
  }
}
```

## Adding New Providers

To add a new provider:

1. Create a new file in the `providers/` directory (e.g., `your_provider.py`)
2. Implement the provider by extending the base classes:

```python
from .base_provider import BaseProvider, BaseModelManager, BaseChat

class YourProvider(BaseProvider):
    def get_provider_name(self) -> str:
        return "yourprovider"
    
    def get_required_config_keys(self) -> List[str]:
        return ["api_key", "api_base"]
    
    def validate_config(self) -> bool:
        # Validate configuration
        return True
    
    def create_model_manager(self) -> BaseModelManager:
        return YourModelManager(self.config)
    
    def create_chat(self) -> BaseChat:
        return YourChat(self.config)
    
    def test_connection(self) -> bool:
        # Test provider connection
        return True
```

3. Restart the application - your provider will be automatically discovered

## Architecture

The application uses a combination of design patterns:

- **Abstract Factory Pattern**: For creating provider-specific components
- **Strategy Pattern**: For runtime provider switching
- **Plugin Architecture**: For automatic provider discovery

### Key Components

- `BaseProvider`: Abstract interface for all providers
- `ProviderFactory`: Manages provider discovery and instantiation
- `ConfigManager`: Handles configuration with provider support
- `ModelManager`: Unified interface for model operations
- `Chat`: Unified interface for chat operations

## Migration

Legacy configurations (flat structure) are automatically migrated to the new provider-based structure on first run.

## License

MIT License - see LICENSE file for details.
