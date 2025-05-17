# RetroChat-v3 - LM Studio Terminal Client

A simple Python-based terminal application to chat with a Large Language Model (LLM) hosted by LM Studio.

## Features

*   Connects to a running LM Studio instance.
*   Basic command-line chat interface.
*   Maintains conversation history for context.
*   Structured for easy modification and upgrades.

## Prerequisites

*   Python 3.7+
*   LM Studio installed and running with a model loaded.
*   LM Studio API server enabled (usually at `http://localhost:1234/v1` by default, but configurable).

## Setup

1.  **Clone the repository or download the files.**
2.  **Navigate to the project directory:**
    ```bash
    cd path/to/Retrochat-v3
    ```
3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate it:
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure the API endpoint (if necessary):**
    Open `config.py` and modify `API_BASE_URL` if your LM Studio server is not running on `http://192.168.1.82:1234/v1`.
    You can also adjust `MODEL_NAME` if you want to specify a particular model loaded in LM Studio, though LM Studio often handles this automatically based on what's loaded.

## Running the Application

1.  Ensure your LM Studio API server is running.
2.  Run the main script:
    ```bash
    python main.py
    ```
3.  Start chatting! Type `exit` or `quit` to end the session.

## Project Structure

*   `main.py`: Entry point of the application.
*   `config.py`: Stores configuration like API endpoints and model parameters.
*   `llm_client.py`: Handles all communication with the LM Studio API.
*   `terminal_ui.py`: Manages the user interface in the terminal.
*   `requirements.txt`: Lists Python package dependencies.
*   `README.md`: This file.

## Future Enhancements (Ideas)

*   Streaming responses for a more interactive feel.
*   More sophisticated error handling and logging.
*   Ability to switch models from the UI.
*   Saving/loading chat history.
*   GUI implementation (e.g., using Tkinter, PyQt, or a web framework).
