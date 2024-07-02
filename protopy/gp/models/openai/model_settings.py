"""
model_settings.py
path: ~/python_venvs/libs/protolib/protopy/gp/models/openai/model_settings.py
This file contains the settings for the openAI model. 
Import: import protopy.gp.models.openai.model_settings as gp_sts
"""

import yaml, os
import protopy.settings as sts

default_model, d_assi = 'gpt-3.5-turbo-0125', 'openAI'

models = {
    'openAI': {
        'models': {
            '3': ['gpt-3.5-turbo-0125', ''],
            '4': ['gpt-4-1106-preview', ''],
            '4o': ['gpt-4o', ''],
        },
        'meta': {'key_path': os.path.join(sts.secrets_dir, "9_secrets/openai/open_ai_key.yml")}
    },
    'while_ai_0': {
        'models': {
            'l3': ['llama3', 'instructs'],
            'l3b': ['llama3:70b', 'instructs'],
            'dl3': ['dolphin-llama3', 'instructs'],
            'dl3b': ['llama3:70b', 'instructs'],
            'dl3k': ['dolphin-llama3:8b-256k', 'instructs'],
            'm8': ['mixtral:8x22b', ''],
            'q2b': ['qwen2:72b', ''],
        },
        'meta': {
            'model_address': 'http://WHILE-AI-0:11434/api/generate',
            'models_to_load': ['codellama:70b', 'dolphin-llama3:70b']
        }
    },
    'while_ai_1': {
        'models': {
            'dl3_1': ['dolphin-llama3', 'instructs'],
            'l3_1': ['llama3', 'instructs'],
        },
        'meta': {
            'model_address': 'http://WHILE-AI-1:11434/api/generate',
            'models_to_load': ['llama3:latest', 'dolphin-llama3:latest']
        }
    }
}


def get_api_key(assistant) -> dict:
    with open(models.get(assistant)['meta'].get('key_path'), 'r') as f:
        return yaml.safe_load(f)
