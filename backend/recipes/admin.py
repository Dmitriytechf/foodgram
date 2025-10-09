from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe
from django import forms

from .models import (Favorite, Ingredient, IngredientAmount, Recipe,
                     ShoppingCart, Subscription, Tag)

User = get_user_model()


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'has_recipes'
    LOOKUP_CHOICES = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(ingredient_amounts__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(ingredient_amounts__isnull=True)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов"""
    list_display = ('id', 'name', 'measurement_unit',
                    'recipes_count')
    list_display_links = ('name',)
    list_filter = ('measurement_unit', HasRecipesFilter)
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


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return (
            ('fast', 'Быстрые (<30 мин)'),
            ('medium', 'Средние (30-60 мин)'),
            ('long', 'Долгие (>60 мин)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lt=30)
        if self.value() == 'medium':
            return queryset.filter(cooking_time__range=(30, 60))
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=60)


class ImagePreviewWidget(forms.FileInput):
    """Кастомный виджет для поля image"""
    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        preview_html = f'''
            <div style="display: flex; align-items: center;">
                <div>
                    <img src="{value.url}" margin-bottom: 10px;
                    style="max-height: 150px; max-width: 150px;">
                </div>
                <div>
                    {input_html}
                </div>
            </div>
        '''
        return mark_safe(preview_html)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов"""
    list_display = (
        'id',
        'name',
        'author_username',
        'favorites_count',
        'cooking_time_min',
        'get_tags_html',
        'get_image_html',
        'get_ingredients_column',
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags', 'created_at',
                   'author', CookingTimeFilter)
    filter_horizontal = ('tags',)
    inlines = (IngredientAmountInline,)
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('name', 'author', 'text', 'cooking_time', 'tags')
        }),
        ('Изображение', {
            'fields': ('image',),
            'classes': ('wide', 'extrapretty'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Используем кастомный виджет для поля image"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['image'].widget = ImagePreviewWidget()
        return form

    @admin.display(description='Продукты')
    def get_ingredients_column(self, recipe):
        """Показывает список ингредиентов рецепта"""
        ingredients = recipe.ingredient_amounts.all()
        return mark_safe('<br>'.join([
            f'{ing.ingredient.name} '
            f'({ing.amount} {ing.ingredient.measurement_unit})'
            for ing in ingredients
        ]))

    @admin.display(description='Автор')
    def author_username(self, recipe):
        return recipe.author.username

    @admin.display(description='Время (мин)')
    def cooking_time_min(self, recipe):
        return recipe.cooking_time

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        """Количество добавлений в избранное"""
        return recipe.favorite.count()

    @admin.display(description='Теги')
    def get_tags_html(self, recipe):
        """Красивые теги"""
        return mark_safe(' '.join(
            tag.name for tag in recipe.tags.all()
        ))

    @mark_safe
    @admin.display(description='Изображения')
    def get_image_html(self, recipe):
        """Миниатюра изображения"""
        if recipe.image:
            return f'<img src="{recipe.image.url}" style="height: 40px;">'


@admin.register(Favorite, ShoppingCart)
class UserRecipeAdmin(admin.ModelAdmin):
    """Админка для избранного и списка покупок"""
    list_display = ('id', 'user', 'recipe', 'recipe_author')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, recipe_instance):
        return recipe_instance.recipe.author


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
        'following_count', 'followers_count', 'get_avatar_html')
    list_filter = ('is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('avatar_preview',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if 'avatar' not in fieldsets[1][1]['fields']:
            fieldsets[1][1]['fields'] = fieldsets[1][1]['fields'] + (
                'avatar_preview', 'avatar'
            )
        return fieldsets

    @mark_safe
    @admin.display(description='Текущий аватар')
    def avatar_preview(self, obj):
        """Превью аватара в форме редактирования"""
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}" style="max-height: 150px;'
                f'max-width: 150px; border-radius: 50%; object-fit: cover;"/>'
            )

    @mark_safe
    @admin.display(description='Аватар')
    def get_avatar_html(self, user):
        """HTML-разметка для аватара"""
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" style="max-height: 50px;'
                f'max-width: 50px; border-radius: 50%; object-fit: cover;" />'
            )

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        """ФИО пользователя в одной колонке"""
        return f'{user.last_name} {user.first_name}'.strip()

    @admin.display(description='Рецепты')
    def recipes_count(self, user):
        """Количество рецептов пользователя"""
        return user.recipes.count()

    @admin.display(description='Подписки')
    def following_count(self, user):
        """Количество подписок пользователя"""
        return user.followings.count()

    @admin.display(description='Подписчики')
    def followers_count(self, user):
        """Количество подписчиков пользователя"""
        return user.followers.count()
