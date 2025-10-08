from django.shortcuts import redirect
from rest_framework import serializers

from .models import Recipe


def recipe_short_link(request, pk):
    """Перенаправление с короткой ссылки на полный рецепт"""
    if not Recipe.objects.filter(id=pk).exists():
        raise serializers.ValidationError(
            f'Рецепт с id {pk} не найден'
        )

    return redirect(f'/api/recipes/{pk}/')
