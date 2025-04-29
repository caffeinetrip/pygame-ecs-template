import json
import os

def read_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def tjson_hook(obj):
    if type(obj) == dict:
        for key in list(obj):
            if (type(key) == str) and (key.translate({ord(k): None for k in ' (),t\0'}).isalnum()) and (key.find(',') != -1) and (key[:2] == 't\0'):
                new_key = tuple(int(v) for v in key.translate({ord(k): None for k in ' ()t\0'}).split(','))
                obj[new_key] = obj[key]
                del obj[key]
    return obj

def tjson_hook_loose(obj):
    if type(obj) == dict:
        for key in list(obj):
            if (type(key) == str) and (key.translate({ord(k): None for k in ' (),t\0'}).isalnum()) and (key.find(',') != -1):
                new_key = tuple(int(v) for v in key.translate({ord(k): None for k in ' ()t\0'}).split(','))
                obj[new_key] = obj[key]
                del obj[key]
    return obj

def tjson_decode(data, loose=False):
    if loose:
        return json.loads(data, object_hook=tjson_hook_loose)
    else:
        return json.loads(data, object_hook=tjson_hook)

def read_tjson(path, loose=False):
    return tjson_decode(read_f(path), loose=loose)

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def read_f(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def write_f(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(data)

def recursive_file_op(path, func, filetype=None):
    data = {}
    base_path = path.split('/')
    for f in os.walk(path):
        wpath = f[0].replace('\\', '/').split('/')
        path_ref = wpath.copy()
        data_ref = data

        # iteratively generate file structure
        while len(path_ref) > len(base_path):
            current_dir = path_ref[len(base_path)]
            if current_dir not in data_ref:
                data_ref[current_dir] = {}
            data_ref = data_ref[current_dir]
            path_ref.pop(len(base_path))

        # load assets
        for asset in f[2]:
            asset_type = asset.split('.')[-1]
            if (asset_type == filetype) or (filetype == None):
                data_ref[asset.split('.')[0]] = func(f[0] + '/' + asset)

    return data
