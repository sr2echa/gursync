# import os
# import requests
# from PIL import Image, UnidentifiedImageError
# import imagehash
# from io import BytesIO
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# from gursync import config
# import base64
# import threading
# import asyncio
# from concurrent.futures import ThreadPoolExecutor

# currently_uploading = set()
# deleted_images = set()
# currently_deleting = set()

# cfg = config.load_config()
# sync_pairs = cfg.get('sync_pairs', [])
# executor = ThreadPoolExecutor(max_workers=len(sync_pairs))  # Adjust based on your needs

# ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.apng', '.tiff', '.mp4', '.mpeg', '.avi', '.webm', '.mov', '.mkv', '.flv', '.avi', '.wmv', '.gifv'}

# async def download_from_imgur(album_id):
#     headers = {
#         'Authorization': f'Client-ID 5dc6065411ee2ab',
#     }
#     response = requests.get(f'https://api.imgur.com/3/album/{album_id}', headers=headers) 
#     return response.json()

# async def upload_to_imgur(file_path, album_id):
#     if file_path in currently_uploading:
#         return
#     currently_uploading.add(file_path)
#     print(f'Uploading {file_path} to album {album_id}')
#     api_key = config.get_api_key()
#     if not api_key:
#         print("API Key not set. Please run `gursync setup` to configure it.")
#         currently_uploading.remove(file_path)
#         return
    
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#     }
#     payload = {
#         'image': base64.b64encode(open(file_path, 'rb').read()).decode('utf-8'),
#         'type': 'base64',
#         'name': os.path.basename(file_path),
#         'title': os.path.basename(file_path),
#         'privacy': '0', # 'public', 'hidden
#         'album': album_id,
#     } 
#     print(payload)
#     # async with aiohttp.ClientSession() as session:
#     #     async with session.post('https://api.imgur.com/3/upload', headers=headers, data=payload) as response:
#     #         if response.status == 200:
#     #             print(f'Successfully uploaded {file_path}')
#     #         else:
#     #             print(f'Failed to upload {file_path}')
#     response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=payload)
#     if response.status_code == 200:
#         print(f'Successfully uploaded {file_path}')
#     else:
#         print(f'Failed to upload {file_path}')
#     currently_uploading.remove(file_path)

# async def delete_from_imgur(image_url, album_id):
#     if image_url in currently_deleting:
#         return
#     if image_url in deleted_images:
#         return
#     currently_deleting.add(image_url)
#     api_key = config.get_api_key()
#     if not api_key:
#         print("API Key not set. Please run `gursync setup` to configure it.")
#         currently_deleting.remove(image_url)
#         return
    
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#         'User-Agent': 'curl/7.84.0',
#         'Accept': '*/*'
#     }
#     print(f'Deleting {image_url} from album {album_id}')
#     response = requests.delete(f'https://api.imgur.com/3/image/{image_url.split("/")[-1].split(".")[0]}', headers=headers) 
#     if response.status_code == 200:
#         print(f'Successfully deleted {image_url}')
#     else:
#         print(f'Failed to delete {image_url}')
#     deleted_images.add(image_url)
#     currently_deleting.remove(image_url)

# class SyncHandler(FileSystemEventHandler):
#     def __init__(self, loop, album_id):
#         super().__init__()
#         self.loop = loop
#         self.album_id = album_id

#     def on_created(self, event):
#         if event.is_directory:
#             return
#         self.handle_event(event.src_path, 'created')

#     def on_deleted(self, event):
#         if event.is_directory:
#             return
#         self.handle_event(event.src_path, 'deleted')

#     async def handle_event(self, file_path, event_type):
#         _, extension = os.path.splitext(file_path)
#         if extension.lower() not in ALLOWED_EXTENSIONS:
#             return
#         print(f'{event_type.capitalize()} {file_path}')
#         if event_type == 'created':
#             # asyncio.run_coroutine_threadsafe(upload_to_imgur(file_path, self.album_id), self.loop)
#             await upload_to_imgur(file_path, self.album_id)
#         if event_type == 'deleted':
#             # asyncio.run_coroutine_threadsafe(self.handle_deletion(file_path), self.loop)
#             await self.handle_deletion(file_path)

#     async def handle_deletion(self, file_path):
#         data = await download_from_imgur(self.album_id)
#         images = data['data']['images']
#         for image in images:
#             if os.path.basename(file_path) in image['title']:
#                 await delete_from_imgur(image['link'], self.album_id)
#                 break

# async def start_sync():
#     observer = Observer()

#     loop = asyncio.get_running_loop()
#     for pair in sync_pairs:
#         directory = pair['directory']
#         event_handler = SyncHandler(loop, pair['album_id'])
#         observer.schedule(event_handler, directory, recursive=True)

#     observer.start()

#     try:
#         await monitor_folders(sync_pairs)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()

# async def monitor_folders(sync_pairs):
#     uploaded_hashes = set()
#     while True:
#         tasks = [check_if_not_synced(pair['directory'], pair['album_id'], uploaded_hashes) for pair in sync_pairs]
#         await asyncio.gather(*tasks)
#         await asyncio.sleep(0.1)

# async def check_if_not_synced(file_path, album_id, uploaded_hashes):
#     data = await download_from_imgur(album_id)
#     images = data['data']['images']
#     data = [x["link"] for x in images]
#     album_hashes = {}

#     for image in images:
#         headers = {
#             'Authorization': f'Client-ID 5dc6065411ee2ab',
#             "user-agent": "curl/7.84.0",
#             "accept": "*/*"
#         }
#         response = requests.get(image['link'], headers=headers)
#         try:
#             response_image = Image.open(BytesIO(response.content))
#             hash = imagehash.average_hash(response_image)
#             if hash in album_hashes and album_hashes[hash] != image['link']:
#                 print(f'Duplicate hash {hash} found for {album_hashes[hash]} and {image['link']}')
#                 await delete_from_imgur(image['link'], album_id)
#             if image['edited'] == 1:
#                 response = requests.get(image['link'], stream=True, headers=headers, allow_redirects=True)
#                 if not response.ok:
#                     print(response)
#                 else:
#                     with open(file_path + "/" + image['title'], 'wb') as handle:
#                         for block in response.iter_content(1024):
#                             if not block:
#                                 break
#                             handle.write(block)
#             album_hashes[hash] = image['link']
#         except UnidentifiedImageError:
#             print(f"Cannot identify image from {image['link']}")

#     file_hashes = {}
        

#     loop = asyncio.get_running_loop()
#     for file in os.listdir(file_path):
#         if file.endswith(tuple(ALLOWED_EXTENSIONS)):
#             file_full_path = os.path.join(file_path, file)
#             hash = await loop.run_in_executor(executor, compute_hash, file_full_path)
#             if hash in file_hashes and file_hashes[hash] != file_full_path:
#                 print(f'Duplicate hash {hash} found for {file_hashes[hash]} and {file_full_path}')
#                 os.remove(file_hashes[hash])
#             file_hashes[hash] = file_full_path

#     print(len(album_hashes), len(file_hashes))
            

#     # for key in album_hashes.keys():
#     #     if key not in file_hashes.keys():
#     #         image = [x for x in images if x['link'] == album_hashes[key]][0]
#     #         if image['edited'] == 1:
#     #             os.remove(file_hashes[key])
#     #             response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
#     #             if not response.ok:
#     #                 print(response)
#     #             else:
#     #                 with open(file_path, 'wb') as handle:
#     #                     for block in response.iter_content(1024):
#     #                         if not block:
#     #                             break
#     #                         handle.write(block)
#     #         print(f'File {album_hashes[key]} has been updated : {file_path}')
#     #         # await delete_from_imgur(album_hashes[key], album_id)

#     #using sets, find the hashes that are in the album but not in the folder
#     only_in_album = set(album_hashes.keys()) - set(file_hashes.keys())
#     only_in_album = only_in_album - currently_deleting
#     only_in_folder = set(file_hashes.keys()) - set(album_hashes.keys())

#     print(f'len(only_in_album): {len(only_in_album)}')
#     print(f'leng(only_in_folder): {len(only_in_folder)}')

#     if len(only_in_album) > 0:
#         for key in only_in_album:
#             #get time stamps of each image in the only_in_album set
#             image = [x for x in images if x['link'] == album_hashes[key]][0]
#             print(image)
#             if image['link'] not in currently_deleting and image['link'] not in deleted_images:
#                 if image['title']==None:
#                     image['title'] = image['id'] + image['type'].replace("image/", ".")

#                 if image['edited'] == 1:
#                     response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
#                     with open(file_path + "/" + image['title'], 'wb') as handle:
#                         for block in response.iter_content(1024):
#                             if not block:
#                                 break
#                             handle.write(block)
#                 else:
#                     # response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
#                     # with open(file_path + "/" + str(image['title']), 'wb') as handle:
#                     #     for block in response.iter_content(1024):
#                     #         if not block:
#                     #             break
#                     #         handle.write(block)
#                     await delete_from_imgur(image['link'], album_id)

#     elif len(only_in_folder)>0:
#         print(f'Images in folder but not in album: {only_in_folder}')
#         for key in only_in_folder:
#             if file_hashes[key] not in currently_uploading:
#                 await upload_to_imgur(file_hashes[key], album_id)
#             else:
#                 print(f'{file_hashes[key]} is currently being uploaded')



# def compute_hash(file_full_path):
#     with Image.open(file_full_path) as img:
#         return imagehash.average_hash(img)

# if __name__ == "__main__":
#     try:
#         asyncio.run(start_sync())
#     except Exception as e:
#         print(f"Error: {e}")


import os
import requests
from PIL import Image, UnidentifiedImageError
import imagehash
import time
from io import BytesIO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gursync import config
import base64

currently_uploading = set()
deleted_images = set()
currently_deleting = set()

cfg = config.load_config()
sync_pairs = cfg.get('sync_pairs', [])

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.apng', '.tiff', '.mp4', '.mpeg', '.avi', '.webm', '.mov', '.mkv', '.flv', '.avi', '.wmv', '.gifv'}

def download_from_imgur(album_id):
    headers = {
        'Authorization': f'Client-ID 5dc6065411ee2ab',
    }
    response = requests.get(f'https://api.imgur.com/3/album/{album_id}', headers=headers) 
    print(response.json()['data']['images_count'])
    return response.json()

def upload_to_imgur(file_path, album_id):
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
    response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=payload)
    if response.status_code == 200:
        print(f'Successfully uploaded {file_path}')
    else:
        print(f'Failed to upload {file_path}')
    currently_uploading.remove(file_path)

def delete_from_imgur(image_url, album_id):
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
    def __init__(self, album_id):
        super().__init__()
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
        # if event_type == 'created':
        #     upload_to_imgur(file_path, self.album_id)
        # if event_type == 'deleted':
        #     self.handle_deletion(file_path)

    def handle_deletion(self, file_path):
        data = download_from_imgur(self.album_id)
        images = data['data']['images']
        for image in images:
            if os.path.basename(file_path) in image['title']:
                delete_from_imgur(image['link'], self.album_id)
                break
s = set()

def start_sync():
    # observer = Observer()

    # for pair in sync_pairs:
    #     directory = pair['directory']
    #     event_handler = SyncHandler(pair['album_id'])
    #     observer.schedule(event_handler, directory, recursive=True)

    # observer.start()
    monitor_folders(sync_pairs)
    # try:
    #     monitor_folders(sync_pairs)
    # except KeyboardInterrupt:
    #     observer.stop()
    # observer.join()

# def monitor_folders(sync_pairs):
#     uploaded_hashes = set()
#     while True:
#         tasks = [check_if_not_synced(pair['directory'], pair['album_id'], uploaded_hashes) for pair in sync_pairs]
#         for task in tasks:
#             task()
#         time.sleep(0.1)
def monitor_folders(sync_pairs):
    uploaded_hashes = set()
    while True:
        for pair in sync_pairs:
            check_if_not_synced(pair['directory'], pair['album_id'], uploaded_hashes)
        time.sleep(12)
        print("1------------------------------1")

def check_if_not_synced(file_path, album_id, uploaded_hashes):
    print("2------------------------------2")
    data = download_from_imgur(album_id)
    images = data['data']['images']
    l = len(images)
    data = [x["link"] for x in images]
    album_hashes = {}

    for image in images:
        headers = {
            'Authorization': f'Client-ID 5dc6065411ee2ab',
            "user-agent": "curl/7.84.0",
            "accept": "*/*"
        }
        response = requests.get(image['link'], headers=headers)
        try:
            response_image = Image.open(BytesIO(response.content))
            hash = imagehash.average_hash(response_image)
            if hash in album_hashes and album_hashes[hash] != image['link']:
                print(f'Duplicate hash {hash} found for {album_hashes[hash]} and {image['link']}')
                delete_from_imgur(image['link'], album_id)
            # if image['edited'] == 1:
            #     response = requests.get(image['link'], stream=True, headers=headers, allow_redirects=True)
            #     if not response.ok:
            #         print(response)
            #     else:
            #         with open(file_path + "/" + image['title'], 'wb') as handle:
            #             for block in response.iter_content(1024):
            #                 if not block:
            #                     break
            #                 handle.write(block)
            # album_hashes[hash] = image['link']
        except UnidentifiedImageError:
            print(f"Cannot identify image from {image['link']}")

    if len(album_hashes) < l:
        s = set()
        while len(s) < l:
            data = download_from_imgur(album_id)
            l = data['data']['images_count']
            images = data['data']['images']
            for image in images:
                headers = {
                    'Authorization': f'Client-ID 5dc6065411ee2ab',
                    "user-agent": "curl/7.84.0",
                    "accept": "*/*"
                }
                response = requests.get(image['link'], headers=headers)
                res_img = Image.open(BytesIO(response.content))
                hash = imagehash.average_hash(res_img)
                if hash not in s:
                    s.add(hash)
                else:
                    delete_from_imgur(image['link'], album_id)

    file_hashes = {}
        

    for file in os.listdir(file_path):
        if file.endswith(tuple(ALLOWED_EXTENSIONS)):
            file_full_path = os.path.join(file_path, file)
            hash = compute_hash(file_full_path)
            if hash in file_hashes and file_hashes[hash] != file_full_path:
                print(f'Duplicate hash {hash} found for {file_hashes[hash]} and {file_full_path}')
                os.remove(file_hashes[hash])
            file_hashes[hash] = file_full_path

    print(len(album_hashes), len(file_hashes))
            

    # for key in album_hashes.keys():
    #     if key not in file_hashes.keys():
    #         image = [x for x in images if x['link'] == album_hashes[key]][0]
    #         if image['edited'] == 1:
    #             os.remove(file_hashes[key])
    #             response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
    #             if not response.ok:
    #                 print(response)
    #             else:
    #                 with open(file_path, 'wb') as handle:
    #                     for block in response.iter_content(1024):
    #                         if not block:
    #                             break
    #                         handle.write(block)
    #         print(f'File {album_hashes[key]} has been updated : {file_path}')
    #         # delete_from_imgur(album_hashes[key], album_id)

    #using sets, find the hashes that are in the album but not in the folder
    only_in_album = set(album_hashes.keys()) - set(file_hashes.keys())
    # only_in_album = only_in_album - currently_deleting
    only_in_folder = set(file_hashes.keys()) - set(album_hashes.keys())

    print(f'len(only_in_album): {len(only_in_album)}')
    print(f'leng(only_in_folder): {len(only_in_folder)}')

    if len(only_in_album) > 0:
        for key in only_in_album:
            #get time stamps of each image in the only_in_album set
            image = [x for x in images if x['link'] == album_hashes[key]][0]
            print(image)
            if image['link'] not in currently_deleting and image['link'] not in deleted_images:
                if image['title']==None:
                    image['title'] = image['id'] + image['type'].replace("image/", ".")

                if image['edited'] == 1:
                    response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
                    with open(file_path + "/" + image['title'], 'wb') as handle:
                        for block in response.iter_content(1024):
                            if not block:
                                break
                            handle.write(block)
                else:
                    # response = requests.get(album_hashes[key], stream=True, headers=headers, allow_redirects=True)
                    # with open(file_path + "/" + str(image['title']), 'wb') as handle:
                    #     for block in response.iter_content(1024):
                    #         if not block:
                    #             break
                    #         handle.write(block)
                    delete_from_imgur(image['link'], album_id)

    if len(only_in_folder)>0:
        print("--------")
        for key in only_in_folder:
            if file_hashes[key] not in currently_uploading:
                if key not in s:
                    upload_to_imgur(file_hashes[key], album_id)
            else:
                print(f'{file_hashes[key]} is currently being uploaded')




def compute_hash(file_full_path):
    with Image.open(file_full_path) as img:
        return imagehash.average_hash(img)

if __name__ == "__main__":
    try:
        start_sync()
    except Exception as e:
        print(f"Error: {e}")