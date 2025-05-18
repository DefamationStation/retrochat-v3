
import re
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

class CodeBlockFormatter:
    def __init__(self):
        self.block_counter = 0
        self.code_blocks = {}  # Map: block_id (int) -> code_string (str)

    def reset(self):
        """Resets the code block counter and stored code blocks."""
        self.block_counter = 0
        self.code_blocks.clear()

    def format_for_display(self, markdown_text: str) -> list:
        """
        Parses markdown text using regex to find code blocks, formats them, 
        and extracts raw code. Interleaving text is treated as Markdown.
        Returns a list of Rich renderables.
        """
        renderables = []
        # Regex to find ```lang\ncode\n``` blocks
        # Captures: group(1)=language (optional), group(2)=code content
        # re.DOTALL allows . to match newlines within the code block
        # \s* after ```lang allows for optional spaces before the newline
        code_block_pattern = re.compile(r"```([a-zA-Z0-9_.-]*)?\s*\n(.*?)\n```", re.DOTALL)
        
        last_idx = 0
        for match in code_block_pattern.finditer(markdown_text):
            start_block, end_block = match.span()
            
            # 1. Add text before this code block (if any)
            if start_block > last_idx:
                preceding_text = markdown_text[last_idx:start_block]
                if preceding_text.strip(): # Avoid adding empty Markdown objects
                    renderables.append(Markdown(preceding_text))

            # 2. Process and add the code block
            language = match.group(1) if match.group(1) else "text" # Default to "text" if no lang specified
            raw_code = match.group(2)

            self.block_counter += 1
            self.code_blocks[self.block_counter] = raw_code
            
            syntax = Syntax(raw_code, language, theme="monokai", line_numbers=True, word_wrap=True)
            # Using title for language, and ensuring panel expands if code is wide (though word_wrap helps)
            panel = Panel(syntax, border_style="bold", expand=False, title=f"Language: {language}")
            renderables.append(panel)
            
            label_text = Text(f"CodeID {self.block_counter}", style="dim cyan")
            renderables.append(label_text)
            renderables.append(Text("\n")) # Newline after label for spacing

            last_idx = end_block

        # 3. Add any remaining text after the last code block
        if last_idx < len(markdown_text):
            trailing_text = markdown_text[last_idx:]
            if trailing_text.strip(): # Avoid adding empty Markdown objects
                renderables.append(Markdown(trailing_text))
        
        # If no code blocks were found by the regex and the original text was not empty,
        # render the whole thing as a single Markdown object.
        # This ensures messages without code blocks are still displayed.
        if not renderables and markdown_text.strip():
            renderables.append(Markdown(markdown_text))
            
        return renderables

    def get_code_by_id(self, block_id: int) -> str | None:
        """Retrieves raw code content by its block number."""
        try:
            return self.code_blocks.get(int(block_id))
        except ValueError:
            return None
