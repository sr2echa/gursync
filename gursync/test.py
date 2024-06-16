from gursync.sync import download_from_imgur
res = download_from_imgur('.','QOkQ4pl')['data']['images']

import json

with open('album.json','w') as f:
    json.dump(res,f)