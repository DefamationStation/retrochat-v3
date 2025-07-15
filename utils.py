import json
import sys
import os

# ANSI color codes
class Colors:
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    @staticmethod
    def supports_color():
        """Check if the terminal supports ANSI color codes"""
        # Check if we're on Windows and enable color support
        if os.name == 'nt':
            try:
                # Enable ANSI escape sequences on Windows 10+
                os.system('color')
                return True
            except:
                return False
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

def colored_text(text, color):
    """Return colored text if terminal supports it, otherwise plain text"""
    if Colors.supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text

def yellow_text(text):
    """Return yellow colored text"""
    return colored_text(text, Colors.YELLOW)

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
