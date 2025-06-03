# RetroChat v3 - Comprehensive Code Documentation

## Overview

RetroChat v3 is a terminal-based chat application that interfaces with LM Studio's local language models. The application provides a rich command-line interface with session management, code block handling, streaming responses, and persistent configuration.

## Architecture Overview

The application follows a modular architecture with clear separation of concerns:

```
retrochat_app/
├── api/           # External API communication
├── core/          # Core business logic and data management
├── ui/            # User interface and display logic
└── utils/         # Utility functions and helpers
```

## Module Documentation

### API Layer (`retrochat_app/api/`)

#### `llm_client.py` - LLM Communication Client

**Purpose**: Handles all communication with the LM Studio API endpoint.

**Key Components**:

- **`LLMClient` class**: Main interface for LLM interactions
  - **Parameter Management**: Maps internal attributes to user settings using `PARAM_KEY_MAP`
  - **Endpoint Configuration**: Manages API base URL and chat completions endpoint
  - **Request Handling**: Supports both streaming and non-streaming responses

**Key Methods**:
- `send_chat_message_full_history()`: Non-streaming chat completion
- `stream_chat_message()`: Streaming chat completion with SSE parsing
- `set_parameter()`: Type-safe parameter setting with validation
- `get_params()`: Returns current configuration state

**Configuration Integration**: Automatically loads user settings on initialization and persists changes via `config_manager`.

### Core Layer (`retrochat_app/core/`)

#### `config_manager.py` - Configuration Management

**Purpose**: Centralized configuration management with user-specific persistence.

**Key Features**:
- **Cross-platform config directory detection** (Windows: `%APPDATA%`, Unix: `~/.config`)
- **Default settings management** with standardized parameter names (lowercase_with_underscores)
- **Runtime configuration updates** with global state synchronization
- **JSON-based persistence** for user settings


#### `session_manager.py` - Session Lifecycle Management

**Purpose**: Manages chat session persistence, history, and code block storage.

**Session Data Structure**:
```python
{
    "conversation_history": [{"role": str, "content": str}],
    "metadata": {
        "created_at": str,
        "name": str,
        "last_modified": str
    },
    "code_blocks": {str: str},  # {global_id: code_content}
    "next_code_block_global_id": int
}
```

**Key Functionality**:
- **Automatic session persistence** with UUID-based identification
- **Last session restoration** on application restart
- **Code block ID management** with global unique identifiers
- **History processing** with automatic code block extraction and tagging

**CRUD Operations**:
- `load_session()`: Session restoration with backward compatibility
- `save_session()`: Atomic session persistence
- `new_session()`: Session creation with metadata initialization
- `delete_session()`: Safe session removal with cleanup

#### `text_processing_utils.py` - Text Processing Engine

**Purpose**: Handles markdown code block processing and thought filtering.

**Code Block Processing**:
- **Regex-based extraction** with language detection
- **Unique ID assignment** for persistent code block references
- **Markdown tag embedding** in format `[CodeID: N]`
- **Content normalization** with whitespace handling

**Thought Processing**:
- **Stream-based token processing** with `<think>` tag filtering
- **Real-time content filtering** for streaming responses
- **Configurable thought display** (show/hide modes)

#### `io_utils.py` - File I/O Abstraction

**Purpose**: Centralized file operations with comprehensive error handling.

**Features**:
- **JSON serialization/deserialization** with encoding safety
- **Directory creation** with recursive path handling
- **Comprehensive error logging** using Python's logging module
- **Type-safe return values** (bool for success, None for failure)

#### `code_block_utils.py` - Code Block Utilities

**Purpose**: Shared regex patterns and extraction logic for code blocks.

**Unified Regex Pattern**:
```python
CODE_BLOCK_PATTERN = re.compile(
    r"```([a-zA-Z0-9_\-\.]*)(?:\s*\[CodeID: (\d+)\])?\s*\n(.*?)\n```",
    re.DOTALL
)
```

### UI Layer (`retrochat_app/ui/`)

#### `terminal_ui.py` - Main UI Controller

**Purpose**: Orchestrates the terminal-based user interface.

**Key Components**:
- **Rich Console Integration**: Advanced terminal formatting with `rich` library
- **History Display**: Formatted conversation history with code block rendering
- **Streaming Interface**: Real-time token display with thought processing
- **Command Delegation**: Routes commands to `command_processor`

**Streaming Architecture**:
```python
def _stream_tokens(self, token_iterable, *, include_thoughts=False) -> str:
    # Processes tokens through text_processing_utils.process_token_stream()
    # Handles thought display based on user preferences
    # Returns accumulated response content
```

#### `command_processor.py` - Command Parsing and Execution

**Purpose**: Handles all slash commands with comprehensive argument parsing.

**Command Categories**:

1. **Configuration Commands**:
   - `/set <param> <value>`: Parameter modification with validation
   - `/system <prompt>`: System prompt management
   - `/params`: Current configuration display

2. **Session Commands**:
   - `/chat new [id]`: Session creation
   - `/chat load <id>`: Session switching
   - `/chat list`: Session enumeration
   - `/chat delete <id>`: Session removal
   - `/chat rename <name>`: Session renaming

3. **Utility Commands**:
   - `/copy <CodeID>`: Clipboard integration
   - `/think <show|hide>`: Thought display toggle
   - `/stream <true|false>`: Streaming mode toggle

**Error Handling**: Uses `shlex` for robust argument parsing with proper quote handling.

#### `code_block_formatter.py` - Code Block Rendering

**Purpose**: Manages code block display formatting and ID management.

**Rendering Pipeline**:
1. **Regex Extraction**: Uses `CODE_BLOCK_PATTERN` for robust parsing
2. **ID Management**: Assigns/retrieves global IDs from session data
3. **Syntax Highlighting**: Integrates with `rich.syntax.Syntax`
4. **Panel Creation**: Generates formatted panels with metadata

**Display Format**:
```
┌─ Language: python ─────────────────────┐
│ 1 │ def hello_world():                 │
│ 2 │     print("Hello, World!")        │
└────────────────────────────────────────┘
CodeID 1
```

#### `display_handler.py` - UI Utilities

**Purpose**: Centralized display functions for consistent formatting.

**Functions**:
- `show_help()`: Command reference display
- `show_system_info()`: Configuration and connection status
- `render_message()`: Role-based message formatting
- `log_error()`: Consistent error display

### Utilities (`retrochat_app/utils/`)

#### `logger_setup.py` - Logging Configuration

**Purpose**: Application-wide logging setup with file-based persistence.

**Features**:
- **Timestamped log files** in `retrochat_app/logs/`
- **Detailed format** with module, function, and line information
- **UTF-8 encoding** for international character support
- **Graceful fallback** if file logging fails

**Log Format**:
```
2025-06-01 13:31:34,123 - module_name - DEBUG - module.function:line - Message
```

## Data Flow Architecture

### Message Processing Flow

1. **User Input** → `terminal_ui.py`
2. **Command Detection** → `command_processor.py` (if slash command)
3. **Session Storage** → `session_manager.py` (add to history)
4. **API Request** → `llm_client.py` (with system prompt + history)
5. **Response Processing** → `text_processing_utils.py` (code block extraction)
6. **Display Rendering** → `code_block_formatter.py` → `terminal_ui.py`

### Configuration Flow

1. **Default Settings** → `config_manager.py` (runtime constants)
2. **User Overrides** → Load from `user_settings.json`
3. **Runtime Changes** → Command processor → Parameter validation → Persistence
4. **Global Sync** → Update API endpoints and client parameters

### Session Management Flow

1. **Application Start** → Load last session or create new
2. **Message Exchange** → Auto-save after each message
3. **Code Block Processing** → Extract, assign IDs, store in session
4. **Session Commands** → CRUD operations with metadata updates

## Error Handling Strategy

### Graceful Degradation
- **Configuration errors**: Fall back to defaults
- **Network errors**: Display user-friendly messages
- **File I/O errors**: Log errors, continue operation
- **JSON parsing errors**: Recover with empty state

### Logging Strategy
- **DEBUG**: Detailed operation traces
- **INFO**: Application lifecycle events
- **WARNING**: Recoverable issues
- **ERROR**: Failures requiring attention

## Security Considerations

### Input Validation
- **Command parsing**: Uses `shlex` for shell injection prevention
- **Parameter validation**: Type checking before API calls
- **File paths**: Directory traversal protection

### Data Protection
- **Local storage only**: No external data transmission except to configured LLM
- **Session isolation**: UUID-based session identification
- **Configuration safety**: Validated parameter ranges

## Performance Optimizations

### Memory Management
- **Streaming responses**: Incremental token processing
- **Session data**: Lazy loading of large histories
- **Code block storage**: Reference-based deduplication

### I/O Efficiency
- **Atomic writes**: JSON file operations are atomic
- **Batched updates**: Session auto-save throttling
- **Directory caching**: OS-specific config path caching

## Extension Points

### Adding New Commands
1. Add command handler to `command_processor.py`
2. Implement validation and execution logic
3. Update help text in `display_handler.py`

### Adding New Parameters
1. Add default value to `config_manager.py`
2. Update `PARAM_KEY_MAP` in `llm_client.py`
3. Implement validation in `set_parameter()`

### Adding New Display Formats
1. Extend `code_block_formatter.py` for new content types
2. Add rendering logic to `terminal_ui.py`
3. Update text processing in `text_processing_utils.py`

## Adding Providers

RetroChat supports multiple backend providers for API requests. Use
`/provider add <name> <type> <api_base_url> [chat_endpoint]` to create a new
provider configuration. The command writes a JSON file and opens it in your
default editor for customization. Activate a provider with
`/provider select <name>` once the configuration is saved.

Example configuration for the OpenRouter service:

```json
{
    "name": "OpenRouter",
    "type": "openai",
    "api_base_url": "https://openrouter.ai/api/v1",
    "chat_completions_endpoint": "https://openrouter.ai/api/v1/chat/completions",
    "headers": { "Authorization": "Bearer <OPENROUTER_API_KEY>" },
    "params": { "model": "deepseek/deepseek-chat-v3-0324:free" }
}
```

Example configuration for a local Ollama instance:

```json
{
    "name": "Local Ollama",
    "type": "ollama",
    "api_base_url": "http://localhost:11434",
    "chat_completions_endpoint": "http://localhost:11434/api/generate",
    "params": { "model": "llama3" }
}
```

Provider configuration files are stored under `~/.config/Retrochat/providers/`.
You can change the model without editing the JSON by running
`/set model_name <model_id>`.

## Dependencies

### Core Dependencies
- **`requests`**: HTTP client for LM Studio API
- **`rich`**: Terminal formatting and syntax highlighting
- **`colorama`**: Cross-platform terminal color support
- **`pyperclip`**: Clipboard integration

### Standard Library Usage
- **`json`**: Configuration and session persistence
- **`uuid`**: Session identification
- **`shlex`**: Command argument parsing
- **`re`**: Text processing and pattern matching
- **`logging`**: Application logging
- **`datetime`**: Timestamp generation

## Testing Recommendations

### Unit Test Coverage
- **Configuration management**: Setting validation, persistence
- **Text processing**: Code block extraction, thought filtering
- **Session management**: CRUD operations, data integrity
- **Command processing**: Argument parsing, validation

### Integration Test Scenarios
- **End-to-end chat flow**: User input → API → Display
- **Session persistence**: Save/load cycle verification
- **Error recovery**: Network failures, malformed responses
- **Configuration changes**: Runtime parameter updates

## Deployment Considerations

### Environment Setup
- **Python 3.8+**: Required for modern typing and `logging.basicConfig(force=True)`
- **Virtual environment**: Isolated dependency management
- **Cross-platform paths**: Automatic config directory detection

### Configuration Management
- **Default settings**: Sensible defaults for immediate use
- **User customization**: Persistent preference storage
- **Environment variables**: Optional override capability

This documentation provides a comprehensive overview of the RetroChat v3 architecture and implementation details suitable for senior-level development review and maintenance.
