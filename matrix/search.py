import requests


def json_extract(obj, key):
    arr = []
    def extract(obj, arr, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr
    values = extract(obj, arr, key)
    return values

results = []
url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query=university%20ontario&key=AIzaSyAVRKisuCRyGV2StgxlAyQGmLE_Of42yMs'

while True:
    x = requests.get(url)
    y = x.json()
    if y['status'] == "OK":
        results.append(y)
        if 'next_page_token' in y.keys():
            token = y['next_page_token']
            url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query=university%20ontario&key=AIzaSyAVRKisuCRyGV2StgxlAyQGmLE_Of42yMs'
            url += f'&pagetoken={token}'
        else:
            break
    else:
        break

keys = ['name', 'business_status']

for result in results:
    names = json_extract(result, keys)
    for x in keys:
        print(json_extract(result, x))
