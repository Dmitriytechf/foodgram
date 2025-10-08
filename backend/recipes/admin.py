from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, IngredientAmount, Recipe,
                     ShoppingCart, Subscription, Tag)

User = get_user_model()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов"""
    list_display = ('id', 'name', 'measurement_unit',
                    'recipes_count')
    list_display_links = ('name',)
    list_filter = ('measurement_unit',)
    search_fields = ('name', 'measurement_unit')
    ordering = ('name',)

    def get_queryset(self, request):
        """Аннотируем queryset количеством рецептов"""
        return super().get_queryset(request).annotate(
            _recipes_count=Count('ingredient_amounts__recipe',
                                 distinct=True)
        )

    @admin.display(description='В рецептах', ordering='_recipes_count')
    def recipes_count(self, count):
        """Количество рецептов с этим ингредиентом"""
        return count._recipes_count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка тегов"""
    list_display = ('id', 'name', 'slug', 'get_recipes_count')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    ordering = ('name',)

    @admin.display(description='Рецептов')
    def get_recipes_count(self, count):
        """Показывает количество рецептов с этим тегом"""
        return count.recipes.count()


class IngredientAmountInline(admin.TabularInline):
    """Ингредиенты в рецепте inline"""
    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов"""
    list_display = (
        'id',
        'name',
        'author',
        'favorites_count',
        'cooking_time',
        'get_tags_html',
        'get_image_html',
        'get_ingredients_preview',
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags', 'created_at', 'author')
    filter_horizontal = ('tags',)
    inlines = (IngredientAmountInline,)
    ordering = ('-created_at',)

    @admin.display(description='Продукты')
    def get_ingredients_preview(self, ingredients):
        """Показывает список ингредиентов рецепта"""
        ingredients = ingredients.ingredient_amounts.all()[:5]
        return ' '.join([
            f'{ing.ingredient.name} ({ing.amount} '
            f'{ing.ingredient.measurement_unit})'
            for ing in ingredients
        ])

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        """Количество добавлений в избранное"""
        return recipe.favorite.count()

    @admin.display(description='Теги')
    def get_tags_html(self, tags_html):
        """Красивые теги"""
        return mark_safe(' '.join(
            f'{tag.name}'
            for tag in tags_html.tags.all()
        ))

    @mark_safe
    @admin.display(description='Изображения')
    def get_image_html(self, image_html):
        """Миниатюра изображения"""
        if image_html.image:
            return f'<img src="{image_html.image.url}" style="height: 40px;">'


@admin.register(Favorite, ShoppingCart)
class UserRecipeAdmin(admin.ModelAdmin):
    """Админка для избранного и списка покупок"""
    list_display = ('id', 'user', 'recipe', 'recipe_author')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, recipe_author):
        return recipe_author.recipe.author


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для подписок"""
    list_display = ('user', 'author')
    search_fields = ('user__username', 'user__email',
                     'author__username', 'author__email')


@admin.register(User)
class UserAdmin(UserAdmin):
    """Кастомная админка для пользователей с поиском по email и username"""
    list_display = (
        'id', 'username', 'get_full_name', 'email', 'recipes_count',
        'following_count', 'followers_count', 'first_name', 'last_name',
        'is_staff', 'get_avatar_html')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        """ФИО = имя + фамилия"""
        return f"{user.first_name} {user.last_name}".strip() or '—'

    @mark_safe
    @admin.display(description='Аватар')
    def get_avatar_html(self, avatar_html):
        """HTML-разметка для аватара"""
        if avatar_html.avatar:
            return (
                f'<img src="{avatar_html.avatar.url}" style="max-height: 50px;'
                f'max-width: 50px; border-radius: 50%; object-fit: cover;" />'
            )

    @admin.display(description='Рецепты')
    def recipes_count(self, recipes_count):
        """Количество рецептов пользователя"""
        return recipes_count.recipes.count()

    @admin.display(description='Подписки')
    def following_count(self, following_count):
        """Количество подписок пользователя"""
        return following_count.following.count()

    @admin.display(description='Подписчики')
    def followers_count(self, followers_count):
        """Количество подписчиков пользователя"""
        return followers_count.followers.count()
