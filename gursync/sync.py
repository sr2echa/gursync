import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gursync import config

def upload_to_imgur(file_path, album_id):
    api_key = config.get_api_key()
    if not api_key:
        print("API Key not set. Please run 'gursync setup' to configure it.")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    
    with open(file_path, 'rb') as file:
        data = {
            'image': file.read(),
            'album': album_id,
            'type': 'file',
        }
        response = requests.post('https://api.imgur.com/3/image', headers=headers, files=data)
    
    if response.status_code == 200:
        print(f'Uploaded {file_path} to album {album_id}')
    else:
        print(f'Failed to upload {file_path}: {response.json()}')

class SyncHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        self.handle_event(event.src_path, 'modified')

    def on_created(self, event):
        if event.is_directory:
            return
        self.handle_event(event.src_path, 'created')

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.handle_event(event.src_path, 'deleted')

    def handle_event(self, file_path, event_type):
        print(f'{event_type.capitalize()} {file_path}')
        # Add event handling logic (upload to Imgur, etc.)

def start_sync():
    cfg = config.load_config()
    sync_pairs = cfg.get('sync_pairs', [])
    observer = Observer()
    event_handler = SyncHandler()

    for pair in sync_pairs:
        directory = pair['directory']
        observer.schedule(event_handler, directory, recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
            # Add logic to sync pending changes to Imgur
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
