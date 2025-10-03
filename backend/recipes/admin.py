from django.contrib import admin

from .models import Favorite, IngredientAmount, Recipe, ShoppingCart


class IngredientAmountInline(admin.TabularInline):
    """Ингредиенты в рецепте inline"""
    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов"""
    list_display = ('id', 'name', 'author', 'favorites_count', 'cooking_time')
    list_display_links = ('name',)
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags', 'created_at')
    filter_horizontal = ('tags',)
    inlines = (IngredientAmountInline,)
    ordering = ('-created_at',)

    def favorites_count(self, obj):
        """Количество добавлений в избранное"""
        return self.favorites.count()
    favorites_count.short_description = 'В избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранного"""
    list_display = ('id', 'user', 'recipe', 'recipe_author')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    def recipe_author(self, obj):
        return obj.recipe.author
    recipe_author.short_description = 'Автор рецепта'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка списка покупок"""
    list_display = ('id', 'user', 'recipe', 'recipe_author')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    def recipe_author(self, obj):
        return obj.recipe.author
    recipe_author.short_description = 'Автор рецепта'
