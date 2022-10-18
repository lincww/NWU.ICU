from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager


class File(models.Model):
    hash = models.CharField(verbose_name="unique SHA256 hash", max_length=64)
    provider_identity = models.CharField(verbose_name="Provider", max_length=64)  # Has only local now.
    provider_info = models.JSONField(verbose_name="provider Infos")
    provider_name = models.CharField(verbose_name="identity to provider", max_length=64, blank=True)
    path = models.CharField(verbose_name="path to the file", max_length=10240)
    download_count = models.IntegerField(verbose_name="Download Counts.")
    time = models.DateTimeField(verbose_name="Time File Created.")

# Class Entity
class Entity(MPTTModel):
    # Metadata
    name = models.CharField(verbose_name="Display Name", max_length=1024)
    description = models.TextField(blank=True)
    time = models.DateTimeField(verbose_name="Time Entity Created.", blank=True)  # extend File time if blank.

    # For symbol links
    is_symbol_link = models.BooleanField()
    point_address = models.CharField(verbose_name="")

    # Non-folder only things
    is_folder = models.BooleanField()  # If true then belows are blank.
    tags = TaggableManager()
    size = models.IntegerField(verbose_name="Size of the file, by KiB", blank=True)
    hash = models.CharField(verbose_name="SHA256 hash of the file", max_length=100, blank=True)

    # Some website-related info
    download_count = models.IntegerField()
    is_need_review = models.BooleanField(verbose_name="Whether need to be reviewed, which is by user upload.")

    # MPTT things
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['hash']
