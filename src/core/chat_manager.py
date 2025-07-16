import os
import json

class ChatManager:
    def __init__(self, chats_dir='chats'):
        self.chats_dir = chats_dir
        if not os.path.exists(self.chats_dir):
            os.makedirs(self.chats_dir)

    def save_chat(self, chat_name, history):
        with open(os.path.join(self.chats_dir, f"{chat_name}.json"), 'w') as f:
            json.dump(history, f, indent=2)

    def load_chat(self, chat_name):
        try:
            with open(os.path.join(self.chats_dir, f"{chat_name}.json"), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def delete_chat(self, chat_name):
        try:
            os.remove(os.path.join(self.chats_dir, f"{chat_name}.json"))
            return True
        except FileNotFoundError:
            return False

    def list_chats(self):
        chats = [f.replace(".json", "") for f in os.listdir(self.chats_dir) if f.endswith(".json")]
        chats.sort(key=lambda x: os.path.getmtime(os.path.join(self.chats_dir, f"{x}.json")), reverse=True)
        return chats
