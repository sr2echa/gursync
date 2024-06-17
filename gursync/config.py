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
    return load_config().get('access_token')

def set_etag(album_id, directory, etag):
    cfg = load_config()
    for sync_pair in cfg.get('sync_pairs', []):
        if sync_pair['album_id'] == album_id and sync_pair['directory'] == directory:
            sync_pair['etag'] = etag
            break
    save_config(cfg)

def set_api_key(api_key):
    cfg = load_config()
    cfg['access_token'] = api_key
    save_config(cfg)
