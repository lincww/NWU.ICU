from rest_framework import serializers
from models import Entity, File
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)


class EntityList(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()

    class Meta:
        model = Entity
        fields = '__all__'

class