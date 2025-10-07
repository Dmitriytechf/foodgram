from django.utils import timezone


def generate_shopping_list_content(ingredients_queryset, recipes_queryset):
    """Генерирует содержимое списка покупок"""
    current_date = timezone.now().strftime('%d.%m.%Y %H:%M')
    return '\n'.join([
        'Foodgram - Список покупок',
        f'Дата составления: {current_date}',
        '-' * 50,
        '',
        'Ингредиенты:',
        *[
            f"{idx:2d}. {item['name']:<25} "
            f"{item['total_amount']:>5} {item['unit']}"
            for idx, item in enumerate(ingredients_queryset, 1)
        ],
        '',
        '-' * 50,
        '',
        'Рецепты:',
        *[
            f"{idx:2d}. {recipe['name']} (автор: {recipe['author__username']})"
            for idx, recipe in enumerate(recipes_queryset, 1)
        ],
        '',
        '-' * 50,
        f'Всего ингредиентов: {len(ingredients_queryset)}',
        f'Всего рецептов: {len(recipes_queryset)}',
        '-' * 50
    ])
