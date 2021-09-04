from django.db import models


# Class File
class SingleFile(models.Model):
    name = models.CharField(verbose_name="File name", max_length=1024)  # TODO: What actually the max_length should be?
    describe = models.TextField(verbose_name="Description", max_length=10240)
    hash = models.TextField(verbose_name="MD5 hash of the file", max_length=16)
    location = models.CharField(verbose_name="Location of the file", blank=True, max_length=1024)
    tags = models.JSONField(verbose_name="Tags of the file, which is an Array")
    size = models.IntegerField(verbose_name="Size of the file, by KiB")
    time = models.DateTimeField(verbose_name="Time file uploaded")
    storage_provider = models.CharField(verbose_name="Provider of the storage: OSS/QiNiu/etc.", max_length=128)
    storage_uri = models.CharField(verbose_name="URI of the file in given provider", max_length=1024)
    is_deleted = models.BooleanField(verbose_name="While file been deleted, the field is False")
    is_folder = models.BooleanField(verbose_name="Whether this is a folder")
    download_time_count = models.IntegerField()
