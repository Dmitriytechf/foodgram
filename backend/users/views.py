import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Profile, Subscription
from .serializers import (CustomUserSerializer, EmailAuthTokenSerializer,
                          UserWithRecipesSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Кастомный вьюсет пользователя с дополнительными полями"""

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return CustomUserSerializer

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Список моих подписок"""
        user = request.user
        subscriptions = User.objects.filter(
            following__user=user).order_by('-following__created_at')

        # Пагинация
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            subscriptions, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписаться/отписаться на пользователя"""
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Создаем подписку
            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Удаляем подписку
            subscription = Subscription.objects.filter(user=user,
                                                       author=author)
            if not subscription.exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        self.get_object = lambda: request.user
        return self.retrieve(request, *args, **kwargs)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request, *args, **kwargs):
        return super().set_password(request, *args, **kwargs)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        url_name='me-avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, JSONParser]
    )
    def avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method == 'PUT':
            avatar_file = None
            if 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']

            elif 'avatar' in request.data:
                avatar_data = request.data['avatar']

                if (isinstance(avatar_data, str)
                        and avatar_data.startswith('data:image')):
                    try:
                        format, imgstr = avatar_data.split(';base64,')
                        ext = format.split('/')[-1]
                        filename = f"{uuid.uuid4()}.{ext}"
                        avatar_file = ContentFile(
                            base64.b64decode(imgstr),
                            name=filename
                        )
                    except Exception:
                        return Response(
                            {'error': 'Invalid image format'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            if not avatar_file:
                return Response(
                    {'error': 'Avatar file is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                user.refresh_from_db()

            user.profile.avatar = avatar_file
            user.profile.save()

            avatar_url = request.build_absolute_uri(user.profile.avatar.url)

            return Response(
                {'avatar': avatar_url},
                status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            if hasattr(user, 'profile') and user.profile.avatar:
                user.profile.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def logout(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenCreateView(ObtainAuthToken):
    """Кастомный view для получения токена"""
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({'auth_token': token.key})
