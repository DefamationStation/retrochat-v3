from openai import OpenAI

class Chat:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.client = OpenAI(base_url=self.config_manager.get('api_base'), api_key=self.config_manager.get('api_key'))

    def send_message(self, message, history):
        model = self.config_manager.get('default_model')
        if not model:
            print("No default model selected. Please use /models to select one.")
            return

        history.append({"role": "user", "content": message})
        completion = self.client.chat.completions.create(
            model=model,
            messages=history,
            temperature=0.7,
        )
        response = completion.choices[0].message.content
        history.append({"role": "assistant", "content": response})
        return response
