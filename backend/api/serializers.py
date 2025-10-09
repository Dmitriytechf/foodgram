import base64
import uuid
from collections import Counter

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes.constants import MIN_AMOUNT
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Subscription, Tag)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки Base64 изображений"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{uuid.uuid4().hex[:10]}.{ext}'
            )

        return super().to_internal_value(data)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта"""
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_AMOUNT)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    @staticmethod
    def find_duplicates(items, get_id_func=lambda x: x):
        """Находит дублирующиеся элементы"""
        return {
            item_id for item_id, count in Counter(
                get_id_func(item) for item in items
            ).items() if count > 1
        }

    def _validate_no_duplicates(self, data, model, field_name, id_func):
        """Общая функция для проверки дубликатов"""
        duplicates = self.find_duplicates(data, get_id_func=id_func)

        if duplicates:
            duplicate_names = model.objects.filter(
                id__in=duplicates
            ).values_list('name', flat=True)
            raise serializers.ValidationError(
                f'{field_name} не должны повторяться. '
                f'Дублируются: {list(duplicate_names)}'
            )

        return data

    def validate_ingredients(self, ingredients_data):
        """Проверяем что ингредиенты не повторяются"""
        return self._validate_no_duplicates(
            ingredients_data,
            Ingredient,
            'Продукты',
            lambda x: x['id']
        )

    def validate_tags(self, tags_data):
        """Проверяем что теги не повторяются"""
        return self._validate_no_duplicates(
            tags_data,
            Tag,
            'Теги',
            lambda x: x.id
        )

    def create_ingredients(self, recipe, ingredients):
        """Создаем связи рецепта с ингредиентами"""
        IngredientAmount.objects.bulk_create(
            IngredientAmount(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами"""
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = super().create(validated_data)

        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами"""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        # Обновляем теги если переданы
        instance.tags.set(tags)

        # Обновляем ингредиенты если переданы
        instance.ingredient_amounts.all().delete()
        self.create_ingredients(instance, ingredients)

        return super().update(instance, validated_data)


class UserSerializer(BaseUserSerializer):
    """Сериализатор для получения данных пользователя"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, user):
        """Проверяет, подписан ли текущий пользователь на кого-то"""
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=user
            ).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта"""
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id', 'is_subscribed')

    def _check_relation(self, recipe, relation_model):
        """Общий метод для проверки связи пользователь-рецепт"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return relation_model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists()
        return False

    def get_is_favorited(self, recipe):
        """Проверяет, в избранном ли рецепт"""
        return self._check_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        """Проверяет, в корзине ли рецепт"""
        return self._check_relation(recipe, ShoppingCart)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта для подписок"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами для подписок"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            UserSerializer.Meta.fields
            + ('recipes', 'recipes_count')
        )

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя с лимитом"""
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


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для загрузки аватара"""
    avatar = Base64ImageField(required=True)
