import json

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
