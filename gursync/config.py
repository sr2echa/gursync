import os
import json

CONFIG_FILE = os.path.expanduser('~/.gursync/config.json')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_api_key():
    return load_config().get('api_key')

def set_api_key(api_key):
    cfg = load_config()
    cfg['api_key'] = api_key
    save_config(cfg)
