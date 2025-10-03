import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from ingredients.models import Ingredient
from tags.models import Tag
from tags.serializers import TagSerializer
from users.serializers import CustomUserSerializer

from .models import Favorite, IngredientAmount, Recipe, ShoppingCart


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
    amount = serializers.IntegerField(min_value=1)

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
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """Проверяем что ингредиенты не повторяются"""
        ingredients = [item['id'] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )

        return value

    def validate_tags(self, value):
        """Проверяем что теги не повторяются"""
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги не должны повторяться'
            )

        return value

    def create_ingredients(self, recipe, ingredients):
        """Создаем связи рецепта с ингредиентами"""
        IngredientAmount.objects.bulk_create([
            IngredientAmount(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами"""
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами"""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем теги если переданы
        if tags is not None:
            instance.tags.set(tags)

        # Обновляем ингредиенты если переданы
        if ingredients is not None:
            instance.ingredient_amounts.all().delete()
            self.create_ingredients(instance, ingredients)

        return instance


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта"""
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(
        read_only=True
    )
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Проверяет, в избранном ли рецепт"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, в корзине ли рецепт"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта для подписок"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
