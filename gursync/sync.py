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
        "user-agent": "curl/7.84.0",
        "accept": "*/*"
    }
    response = requests.get(f'https://api.imgur.com/3/album/{album_id}', headers=headers)
    print(response.json()['data']['images_count'])
    etag = response.headers['ETag']
    return [response.json(), etag]

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
        'User-Agent': 'curl/7.84.0',
        'Accept': '*/*'
    }
    payload = {
        'image': base64.b64encode(open(file_path, 'rb').read()).decode('utf-8'),
        'type': 'base64',
        'name': os.path.basename(file_path),
        'title': os.path.basename(file_path),
        'privacy': '0',  # 'public', 'hidden
        'album': album_id,
    }
    response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=payload)
    if response.status_code == 200:
        print(f'Successfully uploaded {file_path}')
        image_id = response.json()['data']['id']
        new_file_path = os.path.join(os.path.dirname(file_path), f"{image_id}{os.path.splitext(file_path)[1]}")
        os.rename(file_path, new_file_path)
        print(f'Renamed {file_path} to {new_file_path}')
    else:
        print('\n\n\n\n\n')
        print(response.text)
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

def start_sync():
    monitor_folders(sync_pairs)
    
def monitor_folders(sync_pairs):
    while True:
        for pair in sync_pairs:
            check_if_not_synced(pair['directory'], pair['album_id'], pair['etag'])
        time.sleep(15)

def check_if_not_synced(file_path, album_id, prev_etag):
    file_names = [os.path.splitext(os.path.basename(x))[0] for x in os.listdir(file_path) if x.endswith(tuple(ALLOWED_EXTENSIONS))]
    data, etag = download_from_imgur(album_id)
    if etag == prev_etag:
        print("No changes")
        return
    images = data['data']['images']
    data = [x["id"] for x in images]
    
    album_hashes = {}

    for image in images:
        headers = {
            'Authorization': f'Client-ID 5dc6065411ee2ab',
            "user-agent": "curl/7.84.0",
            "accept": "*/*"
        }
        response = requests.get(image['link'], headers=headers)
        response_image = Image.open(BytesIO(response.content))
        hash = imagehash.average_hash(response_image)
        album_hashes[image['link']] = hash

    file_hashes = {}

    for file in os.listdir(file_path):
        if file.endswith(tuple(ALLOWED_EXTENSIONS)):
            file_full_path = os.path.join(file_path, file)
            hash = compute_hash(file_full_path)
            file_hashes[file_full_path] = hash

    album_set = set(album_hashes.values())
    album_list = list(album_hashes.values())  

    file_keys = file_hashes.keys()
    album_keys = album_hashes.keys()

    
    if len(album_set) == len(album_list):
        print("No album duplicates")
    else:
        for key in album_set:
            while album_list.count(key) > 1:
                print(f'Duplicate hash {key} found in album')
                for image in album_hashes.keys():
                    if album_hashes[image] == key:
                        delete_from_imgur(image, album_id)
                        break
                album_list.remove(key)

    file_set = set(file_hashes.values())
    file_list = list(file_hashes.values())
    if len(file_set) == len(file_list):
        print("No local duplicates")
    else:
        for key in file_set:
            while file_list.count(key) > 1:
                print(f'Duplicate hash {key} found in folder')
                for image in file_keys:
                    if file_hashes[image] == key:
                        os.remove(image)
                        break
                file_list.remove(key)


    for key in album_keys:
        d = [x for x in images if x['link'] == key][0]
        if d['edited'] == 1:
            response = requests.get(key, stream=True, headers=headers, allow_redirects=True)
            if not response.ok:
                print(response)
            else:
                with open(os.path.join(file_path, f"{d['id']}{d['type'].replace('image/', '.')}"), 'wb') as handle:
                    for block in response.iter_content(1024):
                        if not block:
                            break
                        handle.write(block)
                print(f"File {d['id']} has been UPDATED")
                #remove any other file in the directory with the same name but with a different extension
                for file in os.listdir(file_path):
                    if os.path.splitext(os.path.basename(file))[0] == d['id'] and file != f"{d['id']}{d['type'].replace('image/', '.')}":
                        os.remove(os.path.join(file_path, file))


    if data == file_names:
        print("Files are in sync")
    
    else:
        for key in file_keys:
            if key not in album_keys:
                upload_to_imgur(key, album_id)
                print(f'File {key} has been uploaded')
        # for id in file_names:
        #     if id not in data:
        #         key = [x for x in file_keys if os.path.splitext(os.path.basename(x))[0] == id][0]
        #         upload_to_imgur(key, album_id)
        #         print(f'File {key} has been uploaded')
        
        for key in album_keys:
            if key not in file_keys:
                delete_from_imgur(key, album_id)
                #delete from album_*
                # album_keys.remove(key)
                # album_list.remove(album_hashes[key])
                # album_set.remove(album_hashes[key])
                # album_hashes.pop(key)
                print(f'File {key} has been deleted')
    
    config.set_etag(album_id, file_path, etag)



def compute_hash(file_full_path):
    with Image.open(file_full_path) as img:
        return imagehash.average_hash(img)

if __name__ == "__main__":
    try:
        start_sync()
    except Exception as e:
        print(f"Error: {e}")
