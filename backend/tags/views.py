from rest_framework import viewsets

from .models import Tag
from .serializers import TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для тегов.
    Только чтение (list и retrieve).
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
