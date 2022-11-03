from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Entity, File

admin.site.register(Entity, MPTTModelAdmin)
admin.site.register(File)