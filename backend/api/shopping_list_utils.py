from django.utils import timezone


INGREDIENT_FORMAT = "{idx}. {name} {total_amount} {unit}"
RECIPE_FORMAT = "{idx}. {name} (автор: {author})"
SEPARATOR = '-' * 50


def generate_shopping_list_content(ingredients, recipes):
    """Генерирует содержимое списка покупок"""
    current_date = timezone.now().strftime('%d.%m.%Y %H:%M')
    return '\n'.join([
        'Foodgram - Список покупок',
        f'Дата составления: {current_date}',
        SEPARATOR,
        '',
        'Ингредиенты:',
        *[
            INGREDIENT_FORMAT.format(
                idx=idx,
                name=item['name'].capitalize(),
                total_amount=item['total_amount'],
                unit=item['unit']
            )
            for idx, item in enumerate(ingredients, 1)
        ],
        '',
        SEPARATOR,
        '',
        'Рецепты:',
        *[
            RECIPE_FORMAT.format(
                idx=idx,
                name=recipe.name,
                author=recipe.author.username
            )
            for idx, recipe in enumerate(recipes, 1)
        ],
        '',
        SEPARATOR,
        f'Всего ингредиентов: {len(ingredients)}',
        f'Всего рецептов: {len(recipes)}',
        SEPARATOR
    ])
