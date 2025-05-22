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
        tag_open, tag_close = "<think>", "</think>"
        in_think = False
        stash = ""
        full: list[str] = []
        out_started = False  # have we printed a visible char yet?

        def _emit(text: str) -> None:
            nonlocal out_started
            if not out_started:
                text = text.lstrip(" \t\r\n")  # <- trim leading blanks once
                if not text:
                    return
            self.console.print(text, style="yellow", end="", highlight=False, soft_wrap=True)
            out_started = True

        with self.console.status(
            "[yellow]Assistant is thinking...[/yellow]", spinner="dots"
        ) as status:
            for chunk in token_iterable:
                status.stop()

                # out-of-band “thought” packets
                if isinstance(chunk, dict) and chunk.get("type") == "thought":
                    if include_thoughts:
                        render_message(
                            self.console,
                            "system",
                            chunk["content"],
                            is_thought=True,
                            show_thoughts_flag=True,
                        )
                    continue

                if not isinstance(chunk, str):
                    continue

                full.append(chunk)
                if include_thoughts:
                    _emit(chunk)
                    continue

                # strip inline <think>…</think>
                stash += chunk
                while stash:
                    if not in_think:
                        start = stash.find(tag_open)
                        if start == -1:
                            _emit(stash)
                            stash = ""
                        else:
                            if start:
                                _emit(stash[:start])
                            stash = stash[start + len(tag_open) :]
                            in_think = True
                    else:
                        end = stash.find(tag_close)
                        if end == -1:
                            stash = ""  # still inside think: drop everything so far
                        else:
                            stash = stash[end + len(tag_close) :]
                            in_think = False

        self.console.print()  # final newline
        return "".join(full)

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
