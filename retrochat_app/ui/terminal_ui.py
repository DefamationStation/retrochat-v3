"""
Handles terminal-based user interface for the chat application.
"""
import re
import colorama
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from retrochat_app.api.llm_client import LLMClient
from retrochat_app.core.session_manager import SessionManager
from retrochat_app.core.text_processing_utils import process_token_stream

# Import the new handlers and formatter
from .command_processor import process_command
from .display_handler import render_message, log_error
from .code_block_formatter import CodeBlockFormatter

colorama.init(autoreset=True)  # reset ANSI colours after every print


class TerminalUI:
    """
    Manages the chat interface in the terminal.
    """

    def __init__(self, llm_client: LLMClient, session_manager: SessionManager):
        self.llm_client = llm_client
        self.session_manager = session_manager
        self.show_thoughts = False
        self.console = Console()
        self.code_block_formatter = CodeBlockFormatter(
            self.session_manager.current_session_data
        )

    # ──────────────────────────────────────────────────────────────────────
    # History loader
    # ──────────────────────────────────────────────────────────────────────
    def _display_loaded_history(self) -> None:
        history = self.session_manager.get_conversation_history()
        if not history:
            return

        self.console.print("[cyan]Resuming previous session...[/cyan]")
        for msg in history:
            role, content = msg.get("role"), msg.get("content")
            if not (role and content):
                continue

            if role == "user":
                render_message(self.console, "user", content)
                continue

            # assistant
            display = (
                re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
                if not self.show_thoughts
                else re.sub(
                    r"<think>(.*?)</think>",
                    lambda m: colorama.Fore.LIGHTBLACK_EX
                    + "Thinking: "
                    + m.group(1).strip()
                    + colorama.Style.RESET_ALL
                    + " ",
                    content,
                    flags=re.DOTALL,
                )
            )
            if not display:
                continue

            for r in self.code_block_formatter.format_for_display(display):
                if isinstance(r, Panel):
                    self.console.print(r)
                elif isinstance(r, Text) and r.plain.startswith("CodeID"):
                    self.console.print(r)
                else:
                    self.console.print(r, style="yellow")

        self.console.print("[cyan]End of previous session.[/cyan]")

    # ──────────────────────────────────────────────────────────────────────
    # Live token streamer  – hides inline <think>…</think> blocks on demand
    # Strips *leading* blank lines/spaces before the first visible char.
    # ──────────────────────────────────────────────────────────────────────
    def _stream_tokens(self, token_iterable, *, include_thoughts=False) -> str:
        full_response_content: list[str] = []

        with self.console.status(
            "[yellow]Assistant is thinking...[/yellow]", spinner="dots"
        ) as status:
            for processed_chunk in process_token_stream(
                token_iterable, include_thoughts=include_thoughts
            ):
                status.stop()  # Stop spinner as soon as first processed chunk is ready

                if processed_chunk["type"] == "text":
                    self.console.print(
                        processed_chunk["content"],
                        style="yellow",
                        end="",
                        highlight=False,
                        soft_wrap=True,
                    )
                    full_response_content.append(processed_chunk["content"])
                elif processed_chunk["type"] == "thought":
                    # This part assumes render_message can handle thought display
                    # based on the previous logic in _stream_tokens.
                    # If include_thoughts is true, process_token_stream yields these.
                    render_message(
                        self.console,
                        "system",
                        processed_chunk["content"],
                        is_thought=True,
                        show_thoughts_flag=True,  # Ensure this flag is correctly used by render_message
                    )
                    # Optionally, add thought content to full_response if needed for history,
                    # though typically thoughts are not part of the main response content.
                    # For now, let's assume thoughts are for display only during streaming.

        self.console.print()  # final newline
        return "".join(full_response_content)

    # ──────────────────────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────────────────────
    def run(self) -> None:
        render_message(
            self.console, "system", "Welcome to RetroChat! Type /help for commands."
        )

        if self.session_manager.load_session():
            self.code_block_formatter = CodeBlockFormatter(
                self.session_manager.current_session_data
            )
            self._display_loaded_history()
        else:
            self.code_block_formatter = CodeBlockFormatter(
                self.session_manager.current_session_data
            )
            self.code_block_formatter.reset()

        while True:
            try:
                user_input = self.console.input("")
            except (KeyboardInterrupt, EOFError):
                render_message(self.console, "system", "\nExiting chat. Goodbye!")
                break

            if user_input.startswith("/"):
                if process_command(self, user_input):
                    break
                continue
            if not user_input.strip():
                continue

            # ── add user msg to history ───────────────────────────
            self.session_manager.add_message_to_history("user", user_input)

            api_msgs = []
            if self.llm_client.system_prompt:
                api_msgs.append(
                    {"role": "system", "content": self.llm_client.system_prompt}
                )
            api_msgs.extend(
                [{k: v for k, v in m.items() if k in ("role", "content")}
                 for m in self.session_manager.get_conversation_history()]
            )

            try:
                if self.llm_client.stream:
                    assistant_text = self._stream_tokens(
                        self.llm_client.stream_chat_message(api_msgs),
                        include_thoughts=self.show_thoughts,
                    )
                else:
                    with self.console.status(
                        "[yellow]Assistant is thinking...[/yellow]", spinner="dots"
                    ):
                        resp = self.llm_client.send_chat_message_full_history(api_msgs)
                    assistant_text = resp or "Error: No response from LLM."

                # store reply
                self.session_manager.add_message_to_history("assistant", assistant_text)

                # ── pretty-print reply (skip plain text if we already streamed it) ─
                if assistant_text.startswith("Error:"):
                    self.console.print(assistant_text, style="yellow")
                    continue

                to_show = (
                    re.sub(
                        r"<think>(.*?)</think>",
                        lambda m: colorama.Fore.LIGHTBLACK_EX
                        + "Thinking: "
                        + m.group(1).strip()
                        + colorama.Style.RESET_ALL
                        + " ",
                        assistant_text,
                        flags=re.DOTALL,
                    ).strip()
                    if self.show_thoughts
                    else re.sub(
                        r"<think>.*?</think>", "", assistant_text, flags=re.DOTALL
                    ).strip()
                )

                renderables = self.code_block_formatter.format_for_display(to_show)
                if self.llm_client.stream:
                    # plain text already on screen – just show code blocks / labels
                    for r in renderables:
                        if isinstance(r, Panel) or (
                            isinstance(r, Text) and r.plain.startswith("CodeID")
                        ):
                            self.console.print(r)
                else:
                    for r in renderables:
                        if isinstance(r, Panel):
                            self.console.print(r)
                        elif isinstance(r, Text) and r.plain.startswith("CodeID"):
                            self.console.print(r)
                        else:
                            self.console.print(r, style="yellow")

            except Exception as exc:
                log_error(self.console, f"Error during LLM communication: {exc}")
