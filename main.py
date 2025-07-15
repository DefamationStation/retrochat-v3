from config_manager import ConfigManager
from model_manager import ModelManager
from chat import Chat

def main():
    config_manager = ConfigManager()
    model_manager = ModelManager(config_manager)
    chat = Chat(config_manager)
    history = []

    while True:
        user_input = input("> ")
        if user_input == "/models":
            models = model_manager.get_models()
            for i, model in enumerate(models.data):
                print(f"{i}: {model.id}")
            try:
                selection = int(input("Select a model: "))
                model_manager.set_default_model(models.data[selection].id)
                print(f"Default model set to {models.data[selection].id}")
            except (ValueError, IndexError):
                print("Invalid selection.")
        elif user_input == "/exit":
            break
        else:
            response = chat.send_message(user_input, history)
            if response:
                print(response)

if __name__ == "__main__":
    main()
