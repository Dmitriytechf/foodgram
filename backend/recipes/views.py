from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def recipe_short_link(request, pk):
    """Перенаправление с короткой ссылки на полный рецепт"""
    recipe = get_object_or_404(Recipe, id=pk)
    return redirect(recipe)
