from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager

from user.models import User


class File(models.Model):
    hash = models.CharField(verbose_name="Unique SHA256 hash", max_length=128)
    PROVIDER_IDENTITY_CHOICES = (
        ('local', 'local'),
    )
    provider_identity = models.CharField(verbose_name="Provider Identity", max_length=64,
                                         choices=PROVIDER_IDENTITY_CHOICES)
    path = models.CharField(verbose_name="Locale the file in the provider", max_length=10240)
    download_count = models.IntegerField(verbose_name="Download Counts")
    time = models.DateTimeField(verbose_name="Time File Created")
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    size = models.IntegerField(verbose_name="Size of the file, by KiB", blank=True)


# Class Entity
class Entity(MPTTModel):
    # Metadata
    name = models.CharField(verbose_name="Display Name", max_length=1024)
    description = models.TextField(blank=True)
    time = models.DateTimeField(verbose_name="Time Entity Created.", blank=True)  # extend File time if blank.
    file_type = models.IntegerField()  # enum: 0 for folder and 1 for file

    # Non-folder only things
    file = models.ForeignKey(File, on_delete=models.CASCADE, blank=True)
    tags = TaggableManager(blank=True)

    # Some website-related info
    download_count = models.IntegerField(blank=True)
    is_need_review = models.BooleanField(verbose_name="Whether need to be reviewed, which is by user upload.")

    # MPTT things
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']


class DownloadLog(models.Model):
    time = models.DateTimeField()
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
