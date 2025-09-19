import json
import logging
import os
import time
from multiprocessing.pool import ThreadPool
from tqdm import auto
from openai import OpenAI
import openai

import tiktoken

import configparser


# Function to read API key from .config file
def read_api_key_from_config(conf_name="GPT"):
    # Determine the path to the .config file in the user's home directory
    home_directory = os.path.expanduser("language_services/openai_api")
    config_file_path = os.path.join(home_directory, "intro_openai.config")

    # Initialize the configparser
    config = configparser.ConfigParser()

    # Read the API key from the [OpenAI] section of the .config file
    try:
        config.read(config_file_path)
        api_keys = dict(config.items(conf_name))
        return api_keys
    except (configparser.NoSectionError, configparser.NoOptionError):
        return None

# Load API key from .config file
# api_key = read_api_key_from_config()
enc = tiktoken.encoding_for_model("gpt-3.5-turbo-16k")

# if api_key is not None:
#     client = OpenAI(api_key=api_key)
# else:
#     raise ValueError("OpenAI API key is required. Please provide a valid API key.")


class RequestFailure(Exception):
    pass

class OpenAIRequest:
    def __init__(self, api_key, validator, max_attempts=3):
        # validator: to check if valid/conditioned text generated
        # max_attempts: how many times try to get response from openai
        self.api_key = api_key
        self.validator = validator
        self.max_attempts = max_attempts
        self.completion = ''
        self.client = OpenAI(api_key=self.api_key)

    def __call__(self, openai_message, num_of_return=1, backoff=3):
        # openai_message: user defined message to call openai api
        # num_of_return: number of returned generations
        # backoff: to control sleep time, if get APIConnectionError, extend the sleep time
        res = []
        attempts = 0
        while attempts < self.max_attempts and len(res) < num_of_return:
            attempts += 1
            try:
                outputs = self._generate(openai_message, num_of_return - len(res))
            except (openai.error.RateLimitError, openai.error.APIConnectionError):
                time.sleep(backoff)
                backoff *= 2
            else:
                if self.validator:
                    for text in outputs:
                        if self.validator(text):
                            res.append(text)
                        else:
                            self.completion = ''
                else:
                    res.extend(outputs)

                backoff = 3

        if len(res) < num_of_return:
            raise RequestFailure(f'Failed to generate {num_of_return} completions in {attempts} attempts')

        return res

    def batch(self, openai_message, num_of_return=1, n_workers=2):
        # openai_message: message that pass to openai
        # batch call openai api
        # n_workers: batch size, number of threads
        with ThreadPool(n_workers) as pool:
            all_results = list(
                auto.tqdm(
                    pool.imap(self._call_from_batch, [(i, p, num_of_return) for i, p in enumerate(openai_message)]),
                    total=len(openai_message)))

        all_results.sort(key=lambda x: x[0])
        return [sample for _, result in all_results for sample in result]

    def _call_from_batch(self, task):
        i, openai_message, num_of_return = task

        try:
            return (i, self(openai_message, num_of_return))
        except:
            return (i, [None] * num_of_return)


class ChatCompletion(OpenAIRequest):
    #
    #
    def __init__(self,
                 system_prompt,
                 api_key,
                 model='gpt-3.5-turbo-16k',
                 max_tokens=3000,
                 temperature=0.0,
                 top_p=1.,
                 presence_penalty=0.,
                 frequency_penalty=0.,
                 stop_tokens=None,
                 validator=None,
                 max_attempts=1,
                 stream=True
                ):

        super().__init__(api_key=api_key, validator=validator, max_attempts=max_attempts)
        self.system_prompt = system_prompt
        self.model=model
        self.max_tokens=max_tokens
        self.temperature=temperature
        self.top_p=top_p
        self.presence_penalty=presence_penalty
        self.frequency_penalty=frequency_penalty
        self.stop_tokens=stop_tokens
        self.stream=stream
        self.api_key = api_key

    def __call__(self, user_message, num_of_return=1):
        return super().__call__(user_message, num_of_return)

    def _generate(self, user_message, num_of_return=1):
        messages = [
            {'role': 'system', 'content': self.system_prompt}
        ]
        args = {
            'model': self.model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'presence_penalty': self.presence_penalty,
            'frequency_penalty': self.frequency_penalty,
            'n': num_of_return,
            'stream': self.stream
        }

        if self.stop_tokens:
            args['stop'] = self.stop_tokens
        try:
            self.generate_full_text(args, user_message)
        except openai.error.InvalidRequestError:
            raise RequestFailure(f'Failed to generate completions with current setting. '
                                 f'Please consider to reduce the prompt length or max_tokens.')

        return [self.completion]

    def generate_full_text(self, args, user_message):
        if isinstance(user_message, str):
            args['messages'].append({'role': 'user', 'content': user_message})
        else:
            args['messages']=user_message
        # for role, msg in user_message:
            # if role not in ['user', 'assistant']:
            #     raise Exception('Role not in [user, assistant]')

        # Estimate token count
        length_token = (15000 - len(enc.encode(json.dumps(args['messages']))))
        if self.max_tokens > length_token:
            self.max_tokens = length_token
            args['max_tokens'] = self.max_tokens

        completion = self.client.chat.completions.create(**args)
        if self.stream:
            stream_comp = ''
            for chunk in completion:
                content = chunk["choices"][0].get("delta", {}).get("content")
                if content is not None:
                    stream_comp += content
                else:
                    break
            self.completion += stream_comp
            if len(enc.encode(stream_comp)) >= self.max_tokens:
                user_message = [msg[1] for msg in user_message if msg[0]=='user'][0]
                # The response exceeds the token limit, truncate the text and continue generating
                user_message = user_message + self.completion[-1000:]
                self.generate_full_text(args, user_message)
            else:
                return
        else:
            self.completion += completion.choices[0].message.content
            if completion.usage.completion_tokens >= self.max_tokens:
                user_message = [msg[1] for msg in user_message if msg[0]=='user'][0]
                # The response exceeds the token limit, truncate the text and continue generating
                user_message = user_message + self.completion[-1000:]
                self.generate_full_text(args, user_message)
            else:
                return
