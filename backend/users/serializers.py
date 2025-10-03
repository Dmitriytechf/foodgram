import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя"""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password'
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор для получения данных пользователя"""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на кого-то"""
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        """Возвращает URL аватара"""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
        return None


class UserWithRecipesSerializer(CustomUserSerializer):
    """Сериализатор пользователя с рецептами для подписок"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = User
        fields = (
            CustomUserSerializer.Meta.fields
            + ('recipes', 'recipes_count')
        )

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя с лимитом"""
        from recipes.serializers import RecipeMinifiedSerializer
        request = self.context.get('request')
        recipes_limit = (
            request.query_params.get('recipes_limit')
            if request
            else None
        )

        recipes = obj.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        return RecipeMinifiedSerializer(recipes, many=True,
                                        context=self.context).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов пользователя"""
        return obj.recipes.count()


class EmailAuthTokenSerializer(serializers.Serializer):
    """Сериализатор для аутентификации по email"""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError('Неверный пароль')
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'Пользователь с таким email не найден')

        return attrs


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для изображений в base64"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=filename)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для загрузки аватара"""
    avatar = Base64ImageField(required=True)
