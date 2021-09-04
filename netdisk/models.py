from django.db import models


# Create your models here.
class file():
    name = models.TextField("File name", max_length=1024)
    describe = models.TextField("Description", max_length=10240)
    hash = models.TextField("MD5 hash of the file", max_length=16)
    location = models.CharField("Location of the file", blank=True)
    tags = models.JSONField("Tags of the file, which is an Array")
    size = models.CharField("Size of the file, by KiB")
    time = models.DateTimeField("Time file uploaded")
    storage_provider = models.CharField("Provider of the storage: OSS/QiNiu/etc.")
    storage_uri = models.CharField("URI of the file in given provider")
    is_deleted = models.BooleanField("While file been deleted, the field is False")
    is_folder = models.BooleanField("Whether this is a folder")
    download_time_count = models.IntegerField("Download time count")

