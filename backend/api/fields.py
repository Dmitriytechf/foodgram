import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для изображений в base64"""

    def to_internal_value(self, data):
        # Проверяем, что это base64 строка
        if isinstance(data, str) and data.startswith('data:image'):
            # Извлекаем формат и данные
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            # Генерируем имя файла
            filename = f'{uuid.uuid4()}.{ext}'

            # Декодируем base64
            data = ContentFile(base64.b64decode(imgstr), name=filename)

        return super().to_internal_value(data)
