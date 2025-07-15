from openai import OpenAI
from utils import yellow_text


class Chat:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.client = OpenAI(base_url=self.config_manager.get('api_base'), api_key=self.config_manager.get('api_key'))

    def send_message(self, message, history):
        model = self.config_manager.get('default_model')
        if not model:
            print("No default model selected. Please use /models to select one.")
            return

        if not history:
            history.append({"role": "system", "content": self.config_manager.get('system_prompt')})

        history.append({"role": "user", "content": message})
        completion = self.client.chat.completions.create(
            model=model,
            messages=history,
            temperature=0.7,
            stream=self.config_manager.get('stream')
        )
        if self.config_manager.get('stream'):
            response = ''
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    print(yellow_text(content), end='', flush=True)
                    response += content
            print()
        else:
            response = completion.choices[0].message.content
            print(yellow_text(response))
        history.append({"role": "assistant", "content": response})
        return response
