from rest_framework import serializers

from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)

    def validate_name(self, value):
        if len(value) > 32:
            raise serializers.ValidationError(
                "Название тега не должно превышать 32 символов")
        return value

    def validate_slug(self, value):
        if len(value) > 32:
            raise serializers.ValidationError(
                "Slug не должно превышать 32 символов")
        return value
