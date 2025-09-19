import re
import os
import configparser
from zhipuai import ZhipuAI


# Function to read API key from .config file
def read_api_key_from_config(conf_name="GLM"):
    # Determine the path to the .config file in the user's home directory
    config_file_path = os.path.join(os.path.dirname(__file__),  "chatglm.config")

    # Initialize the configparser
    config = configparser.ConfigParser()

    # Read the API key from the [OpenAI] section of the .config file
    try:
        config.read(config_file_path)
        api_keys = dict(config.items(conf_name))
        return api_keys
    except (configparser.NoSectionError, configparser.NoOptionError):
        return None


class GlmRequest:
    def __init__(self, api_key, validator=None, max_attempts=3, temperature=0.2, top_p=0.9):
        self.validator = validator
        self.max_attempts = max_attempts
        self.completion = ''
        self.model = "glm-4"
        self.temperature = temperature
        self.top_p = top_p
        self.client = ZhipuAI(api_key=api_key)

    def __call__(self, message, num_of_return=1, backoff=3, stream=True):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=message,
            temperature=self.temperature,
            top_p=self.top_p,
            stream=stream
        )
        res_text = ""
        for chunk in response:
            res_text += chunk.choices[0].delta.content
        return res_text
