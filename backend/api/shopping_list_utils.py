from django.utils import timezone


def generate_shopping_list_content(ingredients, recipes):
    """Генерирует содержимое списка покупок"""
    current_date = timezone.now().strftime('%d.%m.%Y %H:%M')
    return '\n'.join([
        'Foodgram - Список покупок',
        f'Дата составления: {current_date}',
        '-' * 50,
        '',
        'Ингредиенты:',
        *[
            "{idx:2d}. {name:<25} {total_amount:>5} {unit}".format(
                idx=idx,
                name=item['name'].capitalize(),
                total_amount=item['total_amount'],
                unit=item['unit']
            )
            for idx, item in enumerate(ingredients, 1)
        ],
        '',
        '-' * 50,
        '',
        'Рецепты:',
        *[
            "{idx:2d}. {name} (автор: {author})".format(
                idx=idx,
                name=recipe['name'],
                author=recipe['author__username']
            )
            for idx, recipe in enumerate(recipes, 1)
        ],
        '',
        '-' * 50,
        f'Всего ингредиентов: {len(ingredients)}',
        f'Всего рецептов: {len(recipes)}',
        '-' * 50
    ])
