from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SingleFile, PendingFiles
from django.conf import settings
from django.db.models import Avg, Q,F
from django.core import serializers
from django.utils.encoding import escape_uri_path
from django.contrib.auth.mixins import PermissionRequiredMixin
import json
import hashlib
from functools import partial
import os
import urllib.parse
import datetime
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

# TODO: 需要重构 代码结构太乱了

# 这个东西很脏，，，不过能用就行
def my_urlencode(s):
    return urllib.parse.urlencode({'a': s})[2:]


# 抄的https://blog.csdn.net/qq_39248122/article/details/103294615
def md5(data, block_size=65536):
    # 创建md5对象
    m = hashlib.md5()
    # 对django中的文件对象进行迭代
    for item in iter(partial(data.read, block_size), b''):
        # 把迭代后的bytes加入到md5对象中
        m.update(item)
    str_md5 = m.hexdigest()
    return str_md5


def generate_cos_direct_download_link(client, uri):
    response = client.get_presigned_download_url(
        Bucket=settings.PROVIDERS["COS"]["bucketID"],
        Key=uri,
        Expired=1200
    )
    return response


class NetDiskRedirectToDownloadAddress(View):
    # TODO: 现在只写了从cos处下载
    # 其实我个人认为这个地方应该重构，代码框架太乱了
    def get(self, request):
        path_string = request.GET.get('path', "")
        path_string = urllib.parse.urlencode(path_string)
        hash_string = request.GET.get('hash', "")
        if hash_string:
            file = (
                SingleFile.objects.all().order_by('name')
            )
            file = file.filter(hash=hash_string)
            for f in file:
                f.save()
            if not file:
                raise KeyError('No such file')
            client = CosS3Client(CosConfig(
                Region=settings.PROVIDERS["COS"]["COS_REGION"],
                SecretKey=settings.PROVIDERS["COS"]["SECRETKEY"],
                SecretId=settings.PROVIDERS["COS"]["SECRETID"],
            ))
            provider_uri = file[0].storage_uri
            if file[0].size / 1024 / 1024 > 100:  # 文件大于100M
                file.update(download_time_count=F('download_time_count') + 1)
                link = generate_cos_direct_download_link(client, provider_uri)
                return HttpResponseRedirect(link)
            else:
                cos_response = client.get_object(
                    Bucket=settings.PROVIDERS["COS"]["bucketID"],
                    Key=provider_uri
                )
                fp = cos_response['Body'].get_raw_stream()
                res = FileResponse(fp)
                res['Content-Type'] = 'application/octet-stream'
                disposition = "attachment;filename*=utf-8''{}".format(escape_uri_path(file[0].name))
                res['Content-Disposition'] = disposition
                file.update(download_time_count=F('download_time_count') + 1)
                return res
        elif path_string:
            raise KeyError('暂时不支持从path拉取文件')
        else:
            raise KeyError('请输入参数')


class NetDiskListView(View):  # 入口
    model = SingleFile

    # TODO: 增加新建文件夹功能

    def get(self, request):
        path_string = self.request.GET.get('path', "")
        path_string = urllib.parse.unquote(path_string)
        if not path_string:
            path_string = '/'  # 为空时置于/
        file_set = (
            self.model.objects.all().order_by('name')
        )
        file_set = file_set.filter(
            Q(location__startswith=path_string)
        )
        file_set_in_json = serializers.serialize('json', file_set)
        context = {"list_data": file_set_in_json,
                   "raw_data": file_set,
                   "path": path_string
                   }
        return render(request, 'netdisk_list.html', context=context)


class NetDiskUploadView(LoginRequiredMixin, View):
    def get(self, req):
        return render(req, 'netdisk_upload.html')


class NetDiskUploadAction(LoginRequiredMixin, View):
    def handle_uploaded_file(self, file_):
        base_dir = settings.LOCAL_UPLOAD_BASE_DIR
        # 存在重复文件名时给文件后缀加_1 屎山罢了
        file_name = file_.name
        file_path = os.path.join(base_dir, file_name)
        is_file_exist = os.path.exists(file_path)
        file_name_extension = 1
        while is_file_exist:
            file_name_list = file_name.split(".")
            file_name_list.append(file_name_list[-1])
            file_name_list[-2] = str(file_name_extension) + '.'
            file_name_extension += 1
            file_name = "".join(file_name_list)
            file_path = os.path.join(base_dir, file_name)
            print(file_name)
            is_file_exist = os.path.exists(file_path)
        with open(file_path, 'wb+') as destination:  # TODO: 是否应该考虑到多线程问题 open(file_path, 'xb+') 考虑用hash来作为文件名
            # 或是用regex：
            for c in file_.chunks():
                destination.write(c)
        return file_path

    def post(self, request):
        file = request.FILES.get('file', None)
        print(request.FILES)
        if file is None:
            raise KeyError('请选择上传文件')
        file_size = file.size
        is_lt300m = file_size / 1024 / 1024 <= 300
        if not is_lt300m:
            raise KeyError('请不要上传大于300M的文件')

        # 判断是否服务器已有该文件
        MD5 = md5(file)
        is_file_existed = False
        if SingleFile.objects.all().filter(hash=MD5) or PendingFiles.objects.all().filter(hash=MD5):
            is_file_existed = True
            file_path = ""
            # if SingleFile.objects.all().filter(hash=MD5):
            #     file_path = ""
            # else:
            #     file_path = PendingFiles.objects.all().filter(hash=MD5)[0]['path']
        else:
            file_path = self.handle_uploaded_file(file)
        upload_file_model = PendingFiles(name=file.name, path=file_path, user_id=self.request.user.username,
                                         size=file_size, time=datetime.datetime.now(),
                                         hash=MD5, is_existed=is_file_existed,
                                         is_finish=False)  # TODO: description怎么办？
        # TODO: 上传时增加想要上传到的目录
        upload_file_model.save()
        #  如果要加description的话，那前端逻辑得重写
        return HttpResponse('upload succeed')


class SearchFile(View):
    model = SingleFile

    # 基本上从主页那边复制过来的，有问题修那边
    def get(self, request):
        search_string = self.request.GET.get('s', "")
        search_string = urllib.parse.unquote(search_string)
        file_set = (
            self.model.objects.all().order_by('name')
        )
        file_set = file_set.filter(
            Q(name__contains=search_string)
        )
        file_set_in_json = serializers.serialize('json', file_set)
        context = {"list_data": file_set_in_json,
                   "raw_data": file_set,
                   "search_string": search_string
                   }
        return render(request, 'netdisk_search.html', context=context)


class NetDiskPendingFileManager(PermissionRequiredMixin, View):
    permission_required = 'admin'

    def post(self, request):
        post_data = json.loads(request.body)
        # TODO: 如果上传路径不存在即递归创建文件夹
        if post_data['role'] == 'accept':
            data = PendingFiles.objects.all().filter(
                Q(is_finish=False) & Q(is_existed=False) & Q(hash=post_data['hash'])
            )
            client = CosS3Client(CosConfig(
                Region=settings.PROVIDERS["COS"]["COS_REGION"],
                SecretKey=settings.PROVIDERS["COS"]["SECRETKEY"],
                SecretId=settings.PROVIDERS["COS"]["SECRETID"],
            ))
            response = client.upload_file(
                Bucket=settings.PROVIDERS["COS"]["bucketID"],
                LocalFilePath=data[0].path,
                Key=data[0].hash + '/' + data[0].name,
            )
            new_file_model = SingleFile(
                name=data[0].name, description="", hash=data[0].hash, location=post_data['path'], tags=[],
                size=data[0].size, time=data[0].time, storage_provider='cos',
                storage_uri=data[0].hash + '/' + data[0].name, is_deleted=False, is_folder=False, download_time_count=0
            )
            new_file_model.save()
            os.remove(data[0].path)
            data.update(is_finish=True)
            return HttpResponse(response)
        elif post_data['role'] == 'reject':
            data = PendingFiles.objects.all().filter(
                Q(is_finish=False) & Q(is_existed=False) & Q(hash=post_data['hash'])
            )
            os.remove(data[0].path)
            data.update(is_finish=True)
            # TODO: 这里其实可以考虑移动到某固定的文件夹，之后统一清理（即回收站机制）
            return HttpResponse("OK")

    def get(self, request):
        file_name = self.request.GET.get('file', "")
        if file_name:
            file = open(os.path.join(settings.LOCAL_UPLOAD_BASE_DIR, file_name), 'rb')
            return FileResponse(file)

        data_set = PendingFiles.objects.all().filter(
            Q(is_finish=False) & Q(is_existed=False)
        )
        data_set_in_json = serializers.serialize('json', data_set)
        context = {
            "data": data_set_in_json,
            "data_raw": data_set
        }
        return render(request, 'netdisk_review.html', context=context)
