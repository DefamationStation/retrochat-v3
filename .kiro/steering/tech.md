# Technology Stack

## Core Technologies
- **Python 3.x** - Primary programming language
- **OpenAI Python SDK** - For AI model interactions via OpenAI-compatible APIs
- **JSON** - Configuration and chat history storage format

## Dependencies
- `openai` - Official OpenAI Python client library

## Architecture Patterns
- **Manager Pattern** - Separate managers for configuration, models, and chat sessions
- **Command Registry Pattern** - Centralized command handling with registration system
- **Modular Design** - Clear separation of concerns across modules

## Configuration
- JSON-based configuration in `config.json`
- Runtime configuration updates via command interface
- Default API endpoint: `http://localhost:1234/v1` (LM Studio compatible)

## Common Commands

### Setup
```bash
pip install -r requirements.txt
```

### Running
```bash
python main.py
```

### Development
- No build step required - direct Python execution
- Configuration changes persist automatically
- Chat history stored in `chats/` directory as JSON files

## API Compatibility
- Designed for OpenAI-compatible endpoints
- Tested with LM Studio local server
- Supports streaming and non-streaming responses