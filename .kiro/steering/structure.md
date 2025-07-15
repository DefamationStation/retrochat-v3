# Project Structure

## Root Directory Layout
```
├── main.py              # Application entry point and command handling
├── chat.py              # Core chat functionality and OpenAI client
├── chat_manager.py      # Chat session persistence and management
├── config_manager.py    # Configuration loading and saving
├── model_manager.py     # AI model selection and management
├── utils.py             # Utility functions
├── config.json          # Application configuration
├── requirements.txt     # Python dependencies
└── chats/              # Chat history storage directory
    ├── *.json          # Individual chat session files
```

## Module Responsibilities

### Core Modules
- **main.py** - Entry point, command registry, user interface loop
- **chat.py** - OpenAI API integration, message handling, streaming
- **chat_manager.py** - File-based chat persistence (save/load/delete)
- **config_manager.py** - JSON configuration management
- **model_manager.py** - Model listing and selection
- **utils.py** - Shared utility functions

### Data Storage
- **config.json** - Runtime configuration (API keys, endpoints, preferences)
- **chats/*.json** - Individual chat histories with message arrays

## Naming Conventions
- **Files**: Snake_case for Python modules
- **Classes**: PascalCase (e.g., `ConfigManager`, `ChatManager`)
- **Functions**: Snake_case (e.g., `send_message`, `generate_chat_id`)
- **Commands**: Slash prefix with spaces (e.g., `/list models`, `/set stream`)
- **Chat IDs**: 5-character alphanumeric strings

## File Organization Principles
- One class per file for managers
- Clear separation between UI logic (main.py) and business logic
- Configuration and data files in root directory
- Chat histories isolated in dedicated `chats/` subdirectory