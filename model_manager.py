from openai import OpenAI
from config_manager import ConfigManager

class ModelManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.client = OpenAI(base_url=self.config_manager.get('api_base'), api_key=self.config_manager.get('api_key'))

    def get_models(self):
        return self.client.models.list()

    def set_default_model(self, model_id):
        self.config_manager.set('default_model', model_id)
