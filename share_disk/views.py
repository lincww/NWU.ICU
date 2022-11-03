import datetime
import json
import time

from django.db.models import Q
from django.http import JsonResponse

from user.models import User
from .models import Entity, DownloadLog, File


class Token:
    def __init__(self, param: dict | str):
        if isinstance(param, dict):
            self.origin = param
            self.token = self.encrypt(param)
        elif isinstance(param, str):
            self.token = str
            self.origin = self.unencrypt(param)

    def encrypt(self, origin):
        # AES encrypt
        return json.dumps(origin)

    def unencrypt(self, param):
        return json.loads(param)


# TODO: 1.会不会 XSS 2: 用户上传文件的安全性 3. CSRF Token
def quick_json_response(status: int, msg: str, args=None, **kwargs):
    response_json = {'status': status, 'msg': msg}
    if args and isinstance(args, dict):
        response_json.update(args)
    else:
        if kwargs:
            response_json.update(kwargs)
    return JsonResponse(response_json, status=status)


def dive_into_entities(entities, path):
    for i in path:
        entities = entities.filter(name=i)
        if len(entities) != 1:
            raise ValueError('Path Error')
        if entities.file_type != 0:
            raise ValueError('There\'s a file in path.')
        entities = entities[0].get_children()
    return entities


def proceed_path(path: str):
    if (not path.startswith('/')) or (not path.endswith('/')):
        raise ValueError('Wrong Path Info.')
    else:
        return path.strip().split('/')[1:-1]


#  /api/disk/view
def api_disk_view(request):
    if request.method == 'GET':
        # Get the entity root
        entity_root_nodes = Entity.objects.root_nodes()
        # Process the path
        path = request.GET.get('path')
        try:
            path = proceed_path(path)
        except ValueError as e:
            return quick_json_response(400, str(e))
        # Get entity node
        entities = entity_root_nodes
        # Dive into entity
        try:
            entities = dive_into_entities(entities, path)
        except ValueError as e:
            return quick_json_response(400, str(e))
        # Construct Dict
        pure_file_entities = entities.filter(Q(file_type=1) & Q(is_need_review=True))
        result = {
            "status": 200,
            "msg": "Succeed",
            "path": path,
            "file_count": len(pure_file_entities),
            "file_list": [],
        }
        for i in entities:
            file_info = {
                "name": i.name,
                "description": i.description,
                "time": i.time,
                "hash": i.file.hash,
                "file_type": i.file_type,
                "tags": i.tags,
            }
            result['file_list'].append(file_info)
        return JsonResponse(result)
    else:
        return quick_json_response(405, "Method Not Allowed")


# /api/disk/file
def api_disk_file(request):
    if request.method == 'POST':
        path = request.POST.get('path')
        file_name = path.split('/')[-1]
        path = proceed_path(path)
        entity_root_nodes = Entity.objects.root_nodes()
        try:
            entities = dive_into_entities(entity_root_nodes, path)
        except ValueError as e:
            return quick_json_response(400, str(e))
        entity = entities.get(name=file_name)
        file = entity.file
        # Require Login.
        if not request.user.is_authenticated:
            return quick_json_response(403, "Login Required.")
        if file.entity_set.filter(Q(file=file) & Q(is_need_review=True)) and not request.user.has_perm():
            return quick_json_response(404, "File Not Found")
        # TODO: 下载频次限制
        # Add Download Count
        file.download_count += 1
        file.save()
        entity.download_count += 1
        entity.save()
        # Save Download Log
        DownloadLog.objects.create(time=datetime.datetime.now(), entity=entity,
                                   user=User.objects.get(username=request.user.username))
        # Download Dataset
        download_data = {
            'hash': file.hash,
            'expire_time': int(time.time()) + 60 * 60 * 6  # 6 Hours
        }
        # Get download Token
        download_token = Token(download_data).token
        # Generate Download Address
        download_address = 'https://nwu.icu/api/disk/download?token=' + str(download_token)  # TODO: 多源支持
        return quick_json_response(200, "Succeed", download_address=download_address)
    else:
        return quick_json_response(405, "Method Not Allowed")


# /api/disk/upload
# def api_disk_upload(request):
#     if request.method == 'POST':

# /api/disk/download
def api_disk_download(request):
    if request.method == 'GET':
        token = request.GET.get('token')
        if not token:
            return quick_json_response(404, "Wrong token")
        token = Token(token)
        download_data = token.origin
        if download_data['expire_time'] < time.time():
            return quick_json_response(403, "Token expired")
        file = File.objects.get(hash=download_data['hash'])

    else:
        return quick_json_response(405, "Method Not Allowed")