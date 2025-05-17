# Retrochat-v3 Project Overview

This document provides a summary of the Retrochat-v3 project, its structure, and how its components interact. It's intended as a technical overview for understanding the codebase.

## 1. Project Goal

Retrochat-v3 is a Python-based terminal application that allows users to interact with a Large Language Model (LLM) served via an API (e.g., LM Studio). It provides a command-line interface for sending messages to the LLM, receiving responses, and managing model parameters.

## 2. Project Structure

The project is organized into a main script and a primary package `retrochat_app`:

```
.
├── main.py                     # Main entry point for the application.
├── requirements.txt            # Lists Python package dependencies.
├── .gitignore                  # Specifies intentionally untracked files that Git should ignore.
├── retrochat_app/              # Main application package.
│   ├── __init__.py             # Makes retrochat_app a Python package.
│   ├── api/                    # Handles communication with the LLM API.
│   │   ├── __init__.py
│   │   └── llm_client.py       # Contains LLMClient class for API interactions.
│   ├── core/                   # Core functionalities like configuration.
│   │   ├── __init__.py
│   │   └── config_manager.py   # Manages API endpoints, model parameters, and default settings.
│   └── ui/                     # Handles the user interface.
│       ├── __init__.py
│       └── terminal_ui.py      # Contains TerminalUI class for the command-line interface.
└── README.md                   # This file.
```

### Key Files and Directories:

*   **`main.py`**:
    *   The script that initializes and starts the application.
    *   It imports `LLMClient` from `retrochat_app.api` and `TerminalUI` from `retrochat_app.ui`.
    *   It creates instances of these classes and starts the chat interface.

*   **`requirements.txt`**:
    *   Specifies project dependencies. Currently, it includes `requests` for making HTTP calls to the LLM API.

*   **`retrochat_app/`**:
    *   The main package containing all application-specific logic.

*   **`retrochat_app/api/llm_client.py`**:
    *   Defines the `LLMClient` class.
    *   Responsible for constructing and sending requests to the LLM API endpoint (defined in `config_manager.py`).
    *   Handles API parameters like model name, temperature, max tokens, system prompt, etc.
    *   Provides methods to set/get these parameters and manage stop sequences.

*   **`retrochat_app/core/config_manager.py`**:
    *   Stores static configuration values for the application.
    *   Defines the `API_BASE_URL`, `CHAT_COMPLETIONS_ENDPOINT`.
    *   Sets default values for model parameters (`MODEL_NAME`, `TEMPERATURE`, `MAX_TOKENS`, `SYSTEM_PROMPT`, etc.).
    *   These values are used by `LLMClient` as defaults or current settings.

*   **`retrochat_app/ui/terminal_ui.py`**:
    *   Defines the `TerminalUI` class.
    *   Manages the user interaction loop in the terminal.
    *   Prints help messages, prompts for user input.
    *   Parses user input for special commands (e.g., `/help`, `/set`, `/system`, `/exit`).
    *   For regular chat messages, it uses the `LLMClient` to send the message and display the LLM's response.
    *   Maintains a conversation history.

## 3. How it Works (Application Flow)

1.  **Initialization**:
    *   The user runs `python main.py`.
    *   `main.py` instantiates `LLMClient`. The `LLMClient` reads its default configuration (API endpoint, model parameters) from `retrochat_app.core.config_manager.py`.
    *   `main.py` then instantiates `TerminalUI`, passing the `LLMClient` instance to it.

2.  **Chat Loop**:
    *   `TerminalUI.start_chat()` is called, which begins the main interaction loop.
    *   The UI prompts the user for input.

3.  **Input Handling**:
    *   If the input starts with `/`, `TerminalUI` treats it as a command:
        *   Commands like `/set <param> <value>` or `/system <prompt>` modify the settings in the `LLMClient` instance (e.g., `llm_client.set_parameter("temperature", 0.5)`).
        *   Other commands like `/help`, `/info`, `/history` display information to the user.
        *   `/exit` or `/quit` terminates the application.
    *   If the input is not a command, it's treated as a chat message.

4.  **Sending Message to LLM**:
    *   The chat message, along with the current conversation history and configured parameters (system prompt, temperature, etc.), is passed to `LLMClient.send_chat_message()`.
    *   `LLMClient` constructs the JSON payload and makes an HTTP POST request to the LLM API endpoint (e.g., `http://<your-lm-studio-ip>:1234/v1/chat/completions`).

5.  **Receiving and Displaying Response**:
    *   `LLMClient` receives the JSON response from the API.
    *   The response (typically the assistant's message) is returned to `TerminalUI`.
    *   `TerminalUI` prints the assistant's response to the terminal and adds both the user message and assistant response to the conversation history.

6.  **Loop Continuation**:
    *   The loop continues, prompting the user for the next input.

## 4. Configuration

*   Primary configuration is managed in `retrochat_app/core/config_manager.py`.
*   This includes:
    *   `API_BASE_URL`: The base URL for the LM Studio API. **Users need to set this to their LM Studio instance's IP address and port.**
    *   `CHAT_COMPLETIONS_ENDPOINT`: Derived from `API_BASE_URL`.
    *   Default model parameters: `MODEL_NAME`, `TEMPERATURE`, `MAX_TOKENS`, `STREAM`, `SYSTEM_PROMPT`, `TOP_P`, `PRESENCE_PENALTY`, `FREQUENCY_PENALTY`, `STOP_SEQUENCES`.
*   These defaults can be overridden at runtime using `/set` and `/system` commands in the `TerminalUI`.

## 5. Dependencies

*   The project relies on the `requests` library to make HTTP requests to the LLM API. This is listed in `requirements.txt`.
*   To install dependencies: `pip install -r requirements.txt`

## 6. Running the Application

1.  Ensure you have Python installed.
2.  Ensure LM Studio (or a compatible API) is running and accessible.
3.  Update `API_BASE_URL` in `retrochat_app/core/config_manager.py` to point to your LM Studio server if it's not `http://192.168.1.82:1234/v1`.
4.  Install dependencies: `pip install -r requirements.txt`
5.  Navigate to the project's root directory (`Retrochat-v3/`) in your terminal.
6.  Run the application: `python main.py`

This overview should help in understanding the layout and operational flow of the Retrochat-v3 application.
