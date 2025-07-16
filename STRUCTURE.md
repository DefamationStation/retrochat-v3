# Project Structure

This document describes the organized structure of RetroChat v3.

## Directory Structure

```
retrochat-v3/
├── main.py                    # Main entry point
├── config.json               # Configuration file
├── config.example.json       # Example configuration
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── LICENSE                   # License file
├── .gitignore                # Git ignore file
├── chats/                    # Chat history storage
├── src/                      # Source code
│   ├── __init__.py
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── config_manager.py # Configuration management
│   │   ├── model_manager.py  # Model management
│   │   ├── chat_manager.py   # Chat persistence
│   │   └── chat.py           # Chat interface
│   ├── providers/            # AI provider implementations
│   │   ├── __init__.py
│   │   ├── base_provider.py  # Base provider interface
│   │   ├── provider_factory.py # Provider discovery
│   │   ├── lmstudio_provider.py
│   │   └── openrouter_provider.py
│   ├── ui/                   # User interface components
│   │   ├── __init__.py
│   │   ├── command_registry.py # Command registration
│   │   └── commands.py       # Command handlers
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── terminal_colors.py # Terminal color utilities
├── scripts/                  # Setup and utility scripts
│   └── setup_openrouter.py  # OpenRouter setup helper
└── tests/                    # Test files
    └── test_providers.py     # Provider system tests
```

## Component Organization

### Core (`src/core/`)
Contains the main business logic and managers:
- **ConfigManager**: Handles configuration loading, saving, and provider management
- **ModelManager**: Manages AI models and provider switching
- **ChatManager**: Handles chat persistence (save/load/delete)
- **Chat**: Manages chat sessions and AI communication

### Providers (`src/providers/`)
Contains the provider system for different AI services:
- **BaseProvider**: Abstract base classes for all providers
- **ProviderFactory**: Automatic provider discovery and instantiation
- **LMStudioProvider**: Local LM Studio integration
- **OpenRouterProvider**: OpenRouter API integration

### UI (`src/ui/`)
Contains user interface components:
- **CommandRegistry**: Manages slash commands and their handlers
- **CommandHandlers**: Implementation of all command functions

### Utils (`src/utils/`)
Contains utility functions:
- **terminal_colors**: Terminal color formatting utilities

### Scripts (`scripts/`)
Contains setup and utility scripts:
- **setup_openrouter.py**: Interactive OpenRouter configuration

### Tests (`tests/`)
Contains all test files:
- **test_providers.py**: Tests for the provider system

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a clear responsibility
2. **Maintainability**: Code is organized logically and easy to find
3. **Testability**: Tests are in their own directory
4. **Extensibility**: Easy to add new providers, commands, or utilities
5. **Clean Imports**: Clear import hierarchy prevents circular dependencies

## Running the Application

From the project root:
```bash
python main.py
```

## Running Tests

From the project root:
```bash
python tests/test_providers.py
```

## Adding New Providers

1. Create a new file in `src/providers/`
2. Implement the required base classes
3. The provider will be automatically discovered by the factory

## Adding New Commands

1. Add the command handler to `src/ui/commands.py`
2. Register it in `main.py`
3. The command will be available in the application
