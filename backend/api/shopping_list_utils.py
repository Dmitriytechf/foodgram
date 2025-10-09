from django.utils import timezone


RUSSIAN_MONTHS = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}

INGREDIENT_FORMAT = "{idx}. {name} - {total_amount} ({unit})"
RECIPE_FORMAT = "{idx}. {name} (автор: @{author})"
SEPARATOR = '-' * 50


def generate_shopping_list_content(ingredients, recipes):
    """Генерирует содержимое списка покупок"""
    current_date = timezone.now()
    day = current_date.day
    month = RUSSIAN_MONTHS[current_date.month]
    year = current_date.year

    return '\n'.join([
        'Foodgram - Список покупок',
        f'Дата составления: {day} {month} {year}',
        SEPARATOR,
        '',
        'Ингредиенты:',
        *[
            INGREDIENT_FORMAT.format(
                idx=idx,
                name=' '.join(item['name'].split()).capitalize(),
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
