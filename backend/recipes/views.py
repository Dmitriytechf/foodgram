from django.shortcuts import redirect
from django.http import Http404

from .models import Recipe


def recipe_short_link(request, pk):
    """Перенаправление с короткой ссылки на полный рецепт"""
    if not Recipe.objects.filter(id=pk).exists():
        raise Http404(f'Рецепт с id {pk} не найден')

    return redirect(f'/recipes/{pk}/')
