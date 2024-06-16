import os
import time
import requests
from PIL import Image
import imagehash
import urllib.request
from io import BytesIO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gursync import config
import base64
import threading

def download_from_imgur(album_id):
    headers = {
        'Authorization': f'Client-ID 5dc6065411ee2ab',
    }
    response = requests.get(f'https://api.imgur.com/3/album/{album_id}', headers=headers)
    return response.json()

def upload_to_imgur(file_path, album_id):
    print(f'Uploading {file_path} to album {album_id}')
    api_key = config.get_api_key()
    if not api_key:
        print("API Key not set. Please run `gursync setup` to configure it.")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    payload = {
        'image': base64.b64encode(open(file_path, 'rb').read()),
        'type': 'base64',
        'name': os.path.basename(file_path),
        'title': 'Uploaded with blaaa',
        'privacy': '0', # 'public', 'hidden
        'album': album_id,
    }
    response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=payload)

def delete_from_imgur(image_url, album_id):
    api_key = config.get_api_key()
    if not api_key:
        print("API Key not set. Please run `gursync setup` to configure it.")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    print(f'Deleting {image_url} from album {album_id}')
    response = requests.delete(f'	https://api.imgur.com/3/image/{image_url.split("/")[-1].split('.')[0]}', headers=headers)
    print(response.status_code)


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

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.apng', '.tiff', '.mp4', '.mpeg', '.avi', '.webm', '.mov', '.mkv', '.flv', '.avi', '.wmv', '.gifv'}

    def handle_event(self, file_path, event_type):
        _, extension = os.path.splitext(file_path)
        if extension.lower() not in self.ALLOWED_EXTENSIONS:
            return
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

    # observer.start()
    # try:
    # while True:
    #     for pair in sync_pairs:
    #         check_if_not_synced(pair['directory'], pair['album_id'])

    threads = []
    for pair in sync_pairs:
        t = threading.Thread(target=run, args=(pair['directory'], pair['album_id']))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


    # except KeyboardInterrupt:
    #     observer.stop()
    # observer.join()

def run(directory, album_id):
    while True:
        check_if_not_synced(directory, album_id, set())


def check_if_not_synced(file_path, album_id, uploaded_hashes):
    data = download_from_imgur(album_id)['data']['images']
    data = [x["link"]for x in data]
    album_hashes = {}
    for image in data:
        headers = {
            "user-agent": "curl/7.84.0",
            "accept": "*/*"
        }
        r = requests.get(image, stream=True, headers=headers).content
        response = Image.open(BytesIO(r))
        hash = imagehash.average_hash(response)
        album_hashes[hash] = image
            
    file_hashes = {}
    for file in os.listdir(file_path):
        if file.endswith(tuple(SyncHandler.ALLOWED_EXTENSIONS)):
            response = Image.open(file_path + '/' + file)
            hash = imagehash.average_hash(response)
            file_hashes[hash] = file_path + '/' + file
    
    print(len(album_hashes), len(file_hashes))

    #if extra files in directory
    # for key in file_hashes.keys():
    #     if key not in album_hashes.keys():
    #         # print(f'File {file_hashes[key]} not found in album {album_id}')
    #         upload_to_imgur(file_hashes[key], album_id)
    for key in file_hashes.keys():
        if key not in album_hashes.keys() and key not in uploaded_hashes:
            upload_to_imgur(file_hashes[key], album_id)
            uploaded_hashes.add(key)

    for key in album_hashes.keys():
        if key not in file_hashes.keys():
            print(f'File {album_hashes[key]} has been deleted from directory {file_path}')
            delete_from_imgur(album_hashes[key], album_id)


    #if extra files in album
    # for key in album_hashes.keys():
    #     if key not in file_hashes.keys():
    #         print(f'File {album_hashes[key]} not found in directory {file_path}')
    #         response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
    #         if not response.ok:
    #             print(response)
    #         else:
    #             with open(f"{file_path}/{album_hashes[key].split('/')[-1]}", 'wb') as handle:
    #                 for block in response.iter_content(1024):
    #                     if not block:
    #                         break
    #                     handle.write(block)


    # print(album_hashes.values())
    # print(file_hashes.values())

            
        
