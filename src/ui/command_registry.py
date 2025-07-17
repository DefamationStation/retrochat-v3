"""
Command registry for managing slash commands with descriptions.
"""

class CommandRegistry:
    """Registry for managing slash commands with descriptions"""
    def __init__(self):
        self.commands = {}
    
    def register(self, command, description, handler, takes_args=False):
        """Register a command with its description and handler function"""
        self.commands[command] = {
            'description': description,
            'handler': handler,
            'takes_args': takes_args
        }
    
    def get_command(self, command):
        """Get command info by name"""
        return self.commands.get(command)
    
    def get_all_commands(self):
        """Get all registered commands"""
        return self.commands
    
    def execute_command(self, command, *args):
        """Execute a command if it exists"""
        cmd_info = self.get_command(command)
        if cmd_info:
            return cmd_info['handler'](*args)
        return False
