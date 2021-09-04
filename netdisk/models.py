from django.db import models


# Class File
class SingleFile(models.Model):
    name = models.TextField(verbose_name="File name", max_length=1024)
    describe = models.TextField(verbose_name="Description", max_length=10240)
    hash = models.TextField(verbose_name="MD5 hash of the file", max_length=16)
    location = models.CharField(verbose_name="Location of the file", blank=True)
    tags = models.JSONField(verbose_name="Tags of the file, which is an Array")
    size = models.CharField(verbose_name="Size of the file, by KiB")
    time = models.DateTimeField(verbose_name="Time file uploaded")
    storage_provider = models.CharField(verbose_name="Provider of the storage: OSS/QiNiu/etc.")
    storage_uri = models.CharField(verbose_name="URI of the file in given provider")
    is_deleted = models.BooleanField(verbose_name="While file been deleted, the field is False")
    is_folder = models.BooleanField(verbose_name="Whether this is a folder")
    download_time_count = models.IntegerField()

