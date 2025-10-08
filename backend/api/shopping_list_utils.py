from django.utils import timezone


INGREDIENT_FORMAT = "{idx:2d}. {name:<25} {total_amount:>5} {unit}"
RECIPE_FORMAT = "{idx:2d}. {name} (автор: {author})"


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
            INGREDIENT_FORMAT.format(
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
            RECIPE_FORMAT.format(
                idx=idx,
                name=recipe.name,
                author=recipe.author.username
            )
            for idx, recipe in enumerate(recipes, 1)
        ],
        '',
        '-' * 50,
        f'Всего ингредиентов: {len(ingredients)}',
        f'Всего рецептов: {len(recipes)}',
        '-' * 50
    ])
