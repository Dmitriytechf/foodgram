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
    """Фильтр есть ли ингредиент в рецептах"""
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
        if value and hasattr(value, 'url'):
            preview_html = f'''
                <div style="display: flex; align-items: center;">
                    <div>
                        <img src="{value.url}" margin-bottom: 10px;
                        style="max-height: 300px; max-width: 300px;">
                    </div>
                    <div>
                        {input_html}
                    </div>
                </div>
            '''
        else:
            preview_html = f'''
            <div style="margin-bottom: 15px; color: #666;">
                Изображение не загружено
            </div>
            {input_html}
            '''

        return mark_safe(preview_html)


class AuthorUsernameFilter(admin.SimpleListFilter):
    """Фильтр по никам авторов"""
    title = 'Автор'
    parameter_name = 'author'

    def lookups(self, request, model_admin):
        """Возвращает список ников авторов"""
        authors = User.objects.filter(
            recipes__isnull=False
        ).distinct().values_list('username', 'username')[:10]

        return authors

    def queryset(self, request, queryset):
        """Фильтрует по выбранному нику автора"""
        if self.value():
            return queryset.filter(author__username=self.value())
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов"""
    list_display = (
        'id',
        'get_name_html',
        'author_username',
        'favorites_count',
        'cooking_time_min',
        'get_tags_html',
        'get_image_html',
        'get_ingredients_column',
    )
    list_display_links = ('get_name_html',)
    search_fields = ('name', 'author__email', 'author__username',
                     'ingredient_amounts__ingredient__name')
    list_filter = ('tags', 'created_at',
                   AuthorUsernameFilter, CookingTimeFilter)
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
    
    @admin.display(description='Рецепт')
    def get_name_html(self, recipe):
        """Красивое название рецепта с градиентом"""
        return mark_safe(
            f'<span style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%); '
            f'color: white; padding: 8px 16px; border-radius: 25px; '
            f'font-weight: 700; font-size: 14px; display: inline-block; '
            f'box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4); '
            f'border: 2px solid #FFD166; text-shadow: 0 1px 2px rgba(0,0,0,0.1); '
            f'letter-spacing: 0.5px;">'
            f'{recipe.name}</span>'
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
        return mark_safe(
            f'<span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            f'color: white; padding: 8px 16px; border-radius: 25px; '
            f'font-weight: 600; font-size: 13px; display: inline-block; '
            f'box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); '
            f'border: 2px solid #a78bfa; text-shadow: 0 1px 2px rgba(0,0,0,0.1);">'
            f'{recipe.author.username}</span>'
        )

    @admin.display(description='⏱️ Время готовки')
    def cooking_time_min(self, recipe):
        """Цветные бейджи времени готовки"""
        time = recipe.cooking_time
        
        if time < 30:
            gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
            emoji = "⚡"
            label = "БЫСТРЫЙ"
        elif time <= 60:
            gradient = "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)"
            emoji = "🍳"
            label = "СРЕДНИЙ"
        else:
            gradient = "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
            emoji = "⏱️"
            label = "ДОЛГИЙ"
        
        return mark_safe(
            f'<div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">'
            f'<span style="background: {gradient}; color: white; padding: 6px 12px; '
            f'border-radius: 20px; font-weight: 700; font-size: 11px; display: inline-block; '
            f'box-shadow: 0 3px 10px rgba(0,0,0,0.2); border: 2px solid rgba(255,255,255,0.3); '
            f'text-shadow: 0 1px 1px rgba(0,0,0,0.2); letter-spacing: 0.5px;">'
            f'{emoji} {label}</span>'
            f'<span style="font-size: 12px; font-weight: 600; color: #6B7280;">~{time} мин</span>'
            f'</div>'
        )

    @admin.display(description='Руйтинг/В избранном')
    def favorites_count(self, recipe):
        """Количество добавлений в избранное"""
        favorites = recipe.favorite.count()
        if favorites > 10:
            color = "#ff6b6b"
            emoji = "🔥"
        else:
            color = "#4ecdc4" 
            emoji = "⭐"
        
        return mark_safe(
            f'<span style="color: {color}; font-weight: bold;">'
            f'{emoji} {favorites}</span>'
        )

    @admin.display(description='Теги')
    def get_tags_html(self, recipe):
        """Красивые теги"""
        tags = recipe.tags.all()
        if not tags:
            return 'Тег пока не добавлен!'

        # Цветовая схема для конкретных тегов
        tag_colors = {
            'Завтрак': "#F4F80A",
            'Обед': "#2BFF00",
            'Перекус': "#00FFF7",
            'Постное': "#44EC7C",
            'Праздничное': "#FB03FF",
            'Ужин': "#3A6BFE",
            'Чаепитие': "#F48B62",
        }

        tags_html = []
        for tag in tags:
            color = tag_colors.get(tag.name, '#95a5a6')

            tags_html.append(
                f'<span style="background: {color}; color: #080707; '
                f'padding: 4px 8px; border-radius: 16px; font-size: 12px; '
                f'font-weight: 500; margin: 2px; display: inline-block; '
                f'border: 1px solid {color};">'
                f'{tag.name}</span>'
            )

        return mark_safe(' '.join(tags_html))

    @mark_safe
    @admin.display(description='Изображения')
    def get_image_html(self, recipe):
        """Миниатюра изображения"""
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'style="height: 80px; width: 90px; object-fit: cover; '
                f'border-radius: 4px; border: 5px solid #87CEEB;" '
                f'title="{recipe.name}" '
                f'onerror="this.style.display=\'none\'">'
            )
        return 'Изображение не добавлено'


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """Админка для избранного и списка покупок"""
    list_display = ('id', 'user', 'recipe', 'recipe_author')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, recipe_instance):
        return recipe_instance.recipe.author


@admin.register(ShoppingCart)
class ShoppingCartRecipeAdmin(admin.ModelAdmin):
    """Админка для избранного и списка покупок"""
    list_display = ('id', 'recipe_author', 'user', 'recipe')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name',
                     'recipe__author__first_name', 'recipe__author__last_name',
                     'recipe__author__username')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe__author')

    @admin.display(description='Автор')
    def recipe_author(self, recipe_instance):
        author = recipe_instance.recipe.author
        return author.get_full_name() or author.first_name


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
                f'<img src="{obj.avatar.url}" style="max-height: 250px;'
                f'max-width: 150px; border-radius: 50%; object-fit: cover;"/>'
            )

    @mark_safe
    @admin.display(description='Аватар')
    def get_avatar_html(self, user):
        """HTML-разметка для аватара"""
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" style="max-height: 120px;'
                f'max-width: 120px; border-radius: 50%; object-fit: cover;'
                f'border: 3px solid #8b5cf6;" />'
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
