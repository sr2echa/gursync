# import os
# import time
# import requests
# from PIL import Image
# import imagehash
# from io import BytesIO
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# from gursync import config
# import base64
# import threading

# currently_uploading = set()
# currently_deleting = set()

# def download_from_imgur(album_id):
#     headers = {
#         'Authorization': f'Client-ID 5dc6065411ee2ab',
#     }
#     response = requests.get(f'https://api.imgur.com/3/album/{album_id}', headers=headers)
#     return response.json()

# def upload_to_imgur(file_path, album_id):
#     if file_path in currently_uploading:
#         return
#     currently_uploading.add(file_path)
#     print(f'Uploading {file_path} to album {album_id}')
#     api_key = config.get_api_key()
#     if not api_key:
#         print("API Key not set. Please run `gursync setup` to configure it.")
#         return
    
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#     }
#     payload = {
#         'image': base64.b64encode(open(file_path, 'rb').read()),
#         'type': 'base64',
#         'name': os.path.basename(file_path),
#         'title': 'Uploaded with blaaa',
#         'privacy': '0', # 'public', 'hidden
#         'album': album_id,
#     }
#     response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=payload)
#     print(response.status_code)

# def delete_from_imgur(image_url, album_id):
#     if image_url in currently_deleting:
#         return
#     currently_deleting.add(image_url)
#     api_key = config.get_api_key()
#     if not api_key:
#         print("API Key not set. Please run `gursync setup` to configure it.")
#         return
    
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#     }
#     print(f'Deleting {image_url} from album {album_id}')
#     response = requests.delete(f'	https://api.imgur.com/3/image/{image_url.split("/")[-1].split('.')[0]}', headers=headers)
#     currently_deleting.remove(image_url)


# class SyncHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         if event.is_directory:
#             return
#         self.handle_event(event.src_path, 'modified')

#     def on_created(self, event):
#         if event.is_directory:
#             return
#         self.handle_event(event.src_path, 'created')

#     def on_deleted(self, event):
#         if event.is_directory:
#             return
#         self.handle_event(event.src_path, 'deleted')

#     ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.apng', '.tiff', '.mp4', '.mpeg', '.avi', '.webm', '.mov', '.mkv', '.flv', '.avi', '.wmv', '.gifv'}

#     def handle_event(self, file_path, event_type):
#         _, extension = os.path.splitext(file_path)
#         if extension.lower() not in self.ALLOWED_EXTENSIONS:
#             return
#         print(f'{event_type.capitalize()} {file_path}')
#         # Add event handling logic (upload to Imgur, etc.)

# def start_sync():
#     cfg = config.load_config()
#     sync_pairs = cfg.get('sync_pairs', [])
#     observer = Observer()
#     event_handler = SyncHandler()

#     for pair in sync_pairs:
#         directory = pair['directory']
#         observer.schedule(event_handler, directory, recursive=True)

#     # observer.start()
#     # try:
#     # while True:
#     #     for pair in sync_pairs:
#     #         check_if_not_synced(pair['directory'], pair['album_id'])

#     threads = []
#     for pair in sync_pairs:
#         t = threading.Thread(target=run, args=(pair['directory'], pair['album_id']))
#         threads.append(t)
#         t.start()

#     for t in threads:
#         t.join()


#     # except KeyboardInterrupt:
#     #     observer.stop()
#     # observer.join()

# def run(directory, album_id):
#     while True:
#         check_if_not_synced(directory, album_id, set())


# def check_if_not_synced(file_path, album_id, uploaded_hashes):
#     data = download_from_imgur(album_id)['data']['images']
#     data = [x["link"]for x in data]
#     album_hashes = {}
#     for image in data:
#         headers = {
#             "user-agent": "curl/7.84.0",
#             "accept": "*/*"
#         }
#         r = requests.get(image, stream=True, headers=headers).content
#         response = Image.open(BytesIO(r))
#         hash = imagehash.average_hash(response)
#         album_hashes[hash] = image
            
#     file_hashes = {}
#     for file in os.listdir(file_path):
#         if file.endswith(tuple(SyncHandler.ALLOWED_EXTENSIONS)):
#             response = Image.open(file_path + '/' + file)
#             hash = imagehash.average_hash(response)
#             file_hashes[hash] = file_path + '/' + file
    
#     print(len(album_hashes), len(file_hashes))

#     #if extra files in directory
#     # for key in file_hashes.keys():
#     #     if key not in album_hashes.keys():
#     #         # print(f'File {file_hashes[key]} not found in album {album_id}')
#     #         upload_to_imgur(file_hashes[key], album_id)
#     for key in file_hashes.keys():
#         if key not in album_hashes.keys() and key not in uploaded_hashes:
#             upload_to_imgur(file_hashes[key], album_id)
#             uploaded_hashes.add(key)

#     for key in album_hashes.keys():
#         if key not in file_hashes.keys():
#             print(f'File {album_hashes[key]} has been deleted from directory {file_path}')
#             delete_from_imgur(album_hashes[key], album_id)


#     #if extra files in album
#     # for key in album_hashes.keys():
#     #     if key not in file_hashes.keys():
#     #         print(f'File {album_hashes[key]} not found in directory {file_path}')
#     #         response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
#     #         if not response.ok:
#     #             print(response)
#     #         else:
#     #             with open(f"{file_path}/{album_hashes[key].split('/')[-1]}", 'wb') as handle:
#     #                 for block in response.iter_content(1024):
#     #                     if not block:
#     #                         break
#     #                     handle.write(block)


#     # print(album_hashes.values())
#     # print(file_hashes.values())

            
        
import os
import requests
from PIL import Image, UnidentifiedImageError
import imagehash
from io import BytesIO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gursync import config
import base64
import threading
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

currently_uploading = set()
deleted_images = set()
currently_deleting = set()

cfg = config.load_config()
sync_pairs = cfg.get('sync_pairs', [])
executor = ThreadPoolExecutor(max_workers=len(sync_pairs))  # Adjust based on your needs

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.apng', '.tiff', '.mp4', '.mpeg', '.avi', '.webm', '.mov', '.mkv', '.flv', '.avi', '.wmv', '.gifv'}

async def download_from_imgur(session, album_id):
    headers = {
        'Authorization': f'Client-ID 5dc6065411ee2ab',
    }
    async with session.get(f'https://api.imgur.com/3/album/{album_id}', headers=headers) as response:
        return await response.json()

async def upload_to_imgur(file_path, album_id):
    if file_path in currently_uploading:
        return
    currently_uploading.add(file_path)
    print(f'Uploading {file_path} to album {album_id}')
    api_key = config.get_api_key()
    if not api_key:
        print("API Key not set. Please run `gursync setup` to configure it.")
        currently_uploading.remove(file_path)
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    payload = {
        'image': base64.b64encode(open(file_path, 'rb').read()).decode('utf-8'),
        'type': 'base64',
        'name': os.path.basename(file_path),
        'title': os.path.basename(file_path),
        'privacy': '0', # 'public', 'hidden
        'album': album_id,
    } 
    print(payload)
    # async with aiohttp.ClientSession() as session:
    #     async with session.post('https://api.imgur.com/3/upload', headers=headers, data=payload) as response:
    #         if response.status == 200:
    #             print(f'Successfully uploaded {file_path}')
    #         else:
    #             print(f'Failed to upload {file_path}')
    response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=payload)
    if response.status_code == 200:
        print(f'Successfully uploaded {file_path}')
    else:
        print(f'Failed to upload {file_path}')
    currently_uploading.remove(file_path)

async def delete_from_imgur(image_url, album_id):
    if image_url in currently_deleting:
        return
    if image_url in deleted_images:
        return
    currently_deleting.add(image_url)
    api_key = config.get_api_key()
    if not api_key:
        print("API Key not set. Please run `gursync setup` to configure it.")
        currently_deleting.remove(image_url)
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'curl/7.84.0',
        'Accept': '*/*'
    }
    print(f'Deleting {image_url} from album {album_id}')
    response = requests.delete(f'https://api.imgur.com/3/image/{image_url.split("/")[-1].split(".")[0]}', headers=headers) 
    if response.status_code == 200:
        print(f'Successfully deleted {image_url}')
    else:
        print(f'Failed to delete {image_url}')
    deleted_images.add(image_url)
    currently_deleting.remove(image_url)

class SyncHandler(FileSystemEventHandler):
    def __init__(self, loop, album_id):
        super().__init__()
        self.loop = loop
        self.album_id = album_id

    def on_created(self, event):
        if event.is_directory:
            return
        self.handle_event(event.src_path, 'created')

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.handle_event(event.src_path, 'deleted')

    def handle_event(self, file_path, event_type):
        _, extension = os.path.splitext(file_path)
        if extension.lower() not in ALLOWED_EXTENSIONS:
            return
        print(f'{event_type.capitalize()} {file_path}')
    #     if event_type == 'created':
    #         asyncio.run_coroutine_threadsafe(upload_to_imgur(file_path, self.album_id), self.loop)
    #     elif event_type == 'deleted':
    #         asyncio.run_coroutine_threadsafe(self.handle_deletion(file_path), self.loop)

    # async def handle_deletion(self, file_path):
    #     async with aiohttp.ClientSession() as session:
    #         data = await download_from_imgur(session, self.album_id)
    #         images = data['data']['images']
    #         for image in images:
    #             if os.path.basename(file_path) in image['link']:
    #                 await delete_from_imgur(image['link'], self.album_id)
    #                 break

async def start_sync():
    observer = Observer()

    loop = asyncio.get_running_loop()
    for pair in sync_pairs:
        directory = pair['directory']
        event_handler = SyncHandler(loop, pair['album_id'])
        observer.schedule(event_handler, directory, recursive=True)

    observer.start()

    try:
        await monitor_folders(sync_pairs)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

async def monitor_folders(sync_pairs):
    uploaded_hashes = set()
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [check_if_not_synced(session, pair['directory'], pair['album_id'], uploaded_hashes) for pair in sync_pairs]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

async def check_if_not_synced(session, file_path, album_id, uploaded_hashes):
    data = await download_from_imgur(session, album_id)
    images = data['data']['images']
    data = [x["link"] for x in images]
    album_hashes = {}

    for image in data:
        headers = {
            "user-agent": "curl/7.84.0",
            "accept": "*/*"
        }
        response = requests.get(image, headers=headers)
        try:
            response_image = Image.open(BytesIO(response.content))
            hash = imagehash.average_hash(response_image)
            if hash in album_hashes and album_hashes[hash] != image:
                print(f'Duplicate hash {hash} found for {album_hashes[hash]} and {image}')
                await delete_from_imgur(image, album_id)
            album_hashes[hash] = image
        except UnidentifiedImageError:
            print(f"Cannot identify image from {image}")

    file_hashes = {}
        

    loop = asyncio.get_running_loop()
    for file in os.listdir(file_path):
        if file.endswith(tuple(ALLOWED_EXTENSIONS)):
            file_full_path = os.path.join(file_path, file)
            hash = await loop.run_in_executor(executor, compute_hash, file_full_path)
            if hash in file_hashes and file_hashes[hash] != file_full_path:
                print(f'Duplicate hash {hash} found for {file_hashes[hash]} and {file_full_path}')
                os.remove(file_full_path)
            file_hashes[hash] = file_full_path

    print(len(album_hashes), len(file_hashes))

    for key in file_hashes.keys():
        if key not in album_hashes.keys() and key not in uploaded_hashes:
            await upload_to_imgur(file_hashes[key], album_id)
            uploaded_hashes.add(key)

    for key in album_hashes.keys():
        if key not in file_hashes.keys():
            print(f'File {album_hashes[key]} has been deleted from directory {file_path}')
            await delete_from_imgur(album_hashes[key], album_id)

def compute_hash(file_full_path):
    with Image.open(file_full_path) as img:
        return imagehash.average_hash(img)

if __name__ == "__main__":
    try:
        asyncio.run(start_sync())
    except Exception as e:
        print(f"Error: {e}")