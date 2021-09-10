from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import SingleFile, PendingFiles
from django.conf import settings
from django.db.models import Avg, Q
from django.core import serializers
import os
import urllib.parse
import datetime
import oss2


# 这个东西很脏，，，不过能用就行
def my_urlencode(s):
    return urllib.parse.urlencode({'a': s})[2:]


def generate_download_link(**args):
    file = (
        SingleFile.objects.all().order_by('name')
    )
    if args.get('hash', ""):
        file = file.filter(hash=args.get('hash', ""))
        if file.size / 1024 / 1024 > 30:  # 文件大于30M
            

    # elif args.get('path', ""):  # 暂时不支持path拉取文件
    #     path_string = args.get('hash', "")
    #     file_name_string = path_string.split('/')  # Is regex better here?
    #     path_string = "".join(path_string.split('/')[:-1])
    #     file = file.filter()


class RedirectToDownloadAddress(View):
    def get(self, request):
        path_string = request.GET.get('path', "")
        path_string = urllib.parse.urlencode(path_string)
        hash_string = request.GET.get('hash', "")
        if hash_string:
            URL = generate_download_link(hash=hash_string)
        elif path_string:
            raise KeyError('暂时不支持从path拉取文件')
        else:
            raise KeyError('请输入参数')
        return HttpResponseRedirect(URL)


class NetDiskListView(View):  # 入口
    model = SingleFile

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


class UploadView(LoginRequiredMixin, View):
    def get(self, req):
        return render(req, 'netdisk_upload.html')


class UploadAction(LoginRequiredMixin, View):
    def post(self, request):
        # TODO: 在重复上传同一hash的文件时报错
        def handle_uploaded_file(file_):
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
                for c in file_.chunks():
                    destination.write(c)
            return file_path

        file = request.FILES.get('file', None)
        print(request.FILES)
        if file is None:
            raise KeyError('请选择上传文件')
        file_size = file.size
        print(file_size)
        is_lt300m = file_size / 1024 / 1024 <= 300
        if not is_lt300m:
            raise KeyError('请不要上传大于300M的文件')
        file_path = handle_uploaded_file(file)
        upload_file_model = PendingFiles(name=file.name, path=file_path, user_id=self.request.user.username,
                                         size=file.size, time=datetime.datetime.now())  # TODO: description怎么办？
        upload_file_model.save()
        #  如果要加description的话，那前端逻辑得重写
        return HttpResponse('upload succeed')


class SearchFile(View):
    model = SingleFile

    def get(self, request):
        search_string = self.request.GET.get('s', "")
        search_string = urllib.parse.unquote(search_string)
        if not search_string:
            search_string = '/'  # 为空时置于/
        file_set = (
            self.model.objects.all().order_by('name')
        )
        file_set = file_set.filter(
            Q(location__startswith=search_string)
        )
        file_set_in_json = serializers.serialize('json', file_set)
        context = {"list_data": file_set_in_json,
                   "raw_data": file_set,
                   "search_string": search_string
                   }
        return render(request, 'netdisk_list.html', context=context)
