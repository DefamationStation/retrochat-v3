# RetroChat CLI v1.0.0

A minimalistic CLI chat application with modular architecture that connects to LM Studio and other LLM providers.

## Features

- 🚀 **Modular Architecture**: Extensible provider system for different LLM backends
- 🎯 **LM Studio Integration**: Full support for LM Studio's OpenAI-compatible API
- 💬 **Interactive Chat**: Real-time conversations with streaming responses
- 🎛️ **Parameter Control**: Comprehensive chat parameter management (temperature, top_p, max_tokens, etc.)
- 📝 **Conversation Management**: Persistent conversation history and context
- 🌈 **Colored Output**: Beautiful terminal interface with colorama support
- ⚙️ **Configuration Management**: JSON-based configuration with automatic migration

## Installation

### Prerequisites

- Python 3.8 or higher
- LM Studio running with a loaded model

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Quick Start

1. Start LM Studio and load a model
2. Run the application:
   ```bash
   python main.py
   ```
3. Start chatting!

## Configuration

The application uses a `config.json` file that will be automatically created on first run. You can customize:

### Provider Configuration

```json
{
  "default_provider": "lmstudio",
  "providers": {
    "lmstudio": {
      "host": "192.168.1.82",
      "port": 1234,
      "model": null,
      "api_key": null,
      "timeout": 30,
      "base_url": null,
      "use_openai_format": true
    }
  }
}
```

### Chat Parameters

```json
{
  "chat": {
    "system_prompt": "You are a helpful AI assistant.",
    "max_tokens": 8000,
    "temperature": 0.7,
    "top_p": 1.0,
    "top_k": 40,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "repeat_penalty": 1.1,
    "stream": true,
    "stop_sequences": null,
    "seed": null
  }
}
```

## Commands

Use slash commands to control the application:

### Basic Commands
- `/help` - Show available commands
- `/exit` or `/quit` - Exit the application
- `/clear` - Clear conversation history

### Model Management
- `/models` - List available models
- `/model <name>` - Switch to a specific model
- `/model` - Show current model

### Parameter Management
- `/params` - Show current chat parameters
- `/params temperature=0.8` - Set temperature
- `/params max_tokens=4000 temperature=0.5` - Set multiple parameters

### System Information
- `/status` - Show system status
- `/providers` - List available providers
- `/config` - Show current configuration

## Supported Chat Parameters

When using `/params`, you can modify these parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `temperature` | float | Controls randomness (0.0-2.0) | `temperature=0.7` |
| `max_tokens` | int | Maximum response length | `max_tokens=4000` |
| `top_p` | float | Nucleus sampling (0.0-1.0) | `top_p=0.9` |
| `top_k` | int | Top-k sampling | `top_k=40` |
| `frequency_penalty` | float | Reduce repetition (-2.0 to 2.0) | `frequency_penalty=0.5` |
| `presence_penalty` | float | Encourage new topics (-2.0 to 2.0) | `presence_penalty=0.5` |
| `repeat_penalty` | float | Alternative repetition control | `repeat_penalty=1.1` |
| `stream` | bool | Enable streaming responses | `stream=true` |
| `seed` | int | Reproducible outputs | `seed=42` |
| `stop_sequences` | list | Stop generation at sequences | `stop_sequences=\n,###` |

## Architecture

The application follows a modular architecture:

```
src/
├── config.py          # Configuration management
├── chat_manager.py     # Conversation handling
├── commands.py         # Slash command system
├── cli.py             # CLI interface
└── providers/         # Provider system
    ├── __init__.py    # Base classes
    ├── factory.py     # Provider factory
    └── lmstudio.py    # LM Studio provider
```

### Adding New Providers

To add a new provider:

1. Create a new file in `src/providers/`
2. Implement the `ChatProvider` interface
3. The factory will automatically discover it

Example:

```python
from . import ChatProvider, ChatMessage, ChatResponse

class MyProvider(ChatProvider):
    def list_models(self) -> List[str]:
        # Implementation
        pass
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        # Implementation
        pass
    
    # ... other required methods
```

## Development

### Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Test the provider directly
python test_provider.py
```

### Code Structure

- **Providers**: Abstracted backend implementations
- **Chat Manager**: Handles conversation flow and history
- **Commands**: Extensible slash command system
- **Configuration**: JSON-based with automatic migration
- **CLI**: Colored terminal interface with streaming support

## Troubleshooting

### LM Studio Connection Issues

1. Ensure LM Studio is running
2. Check that a model is loaded
3. Verify the host/port in configuration
4. Test connectivity with: `/status`

### Model Not Found

1. List available models: `/models`
2. Switch to an available model: `/model <name>`

### Configuration Issues

1. Check config.json exists and is valid JSON
2. Reset config by deleting config.json (will recreate with defaults)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Roadmap

- [ ] Additional provider support (OpenAI, Anthropic, etc.)
- [ ] Conversation export/import
- [ ] Plugin system
- [ ] Web interface
- [ ] Model fine-tuning integration