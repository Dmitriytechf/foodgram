from django.utils import timezone


RUSSIAN_MONTHS = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}

UNIT_FORMS = {
    'стакан': {'one': 'стакан', 'few': 'стакана', 'many': 'стаканов'},
    'грамм': {'one': 'грамм', 'few': 'грамма', 'many': 'граммов'},
    'ложка': {'one': 'ложка', 'few': 'ложки', 'many': 'ложек'},
    'столовая ложка': {'one': 'столовая ложка', 'few': 'столовые ложки', 'many': 'столовых ложек'},
    'чайная ложка': {'one': 'чайная ложка', 'few': 'чайные ложки', 'many': 'чайных ложек'},
    'штука': {'one': 'штука', 'few': 'штуки', 'many': 'штук'},
    'зубчик': {'one': 'зубчик', 'few': 'зубчика', 'many': 'зубчиков'},
    'пучок': {'one': 'пучок', 'few': 'пучка', 'many': 'пучков'},
    'щепотка': {'one': 'щепотка', 'few': 'щепотки', 'many': 'щепоток'},
    'мл': {'one': 'мл.', 'few': 'мл.', 'many': 'мл.'},
    'л': {'one': 'л.', 'few': 'л.', 'many': 'л.'},
    'г': {'one': 'гр.', 'few': 'гр.', 'many': 'гр.'},
    'кг': {'one': 'кг.', 'few': 'кг.', 'many': 'кг.'},
}


def get_correct_unit_form(amount, unit):
    """Возвращает правильную форму единицы измерения"""
    if unit not in UNIT_FORMS:
        return unit

    if amount % 10 == 1 and amount % 100 != 11:
        return UNIT_FORMS[unit]['one']
    elif 2 <= amount % 10 <= 4 and (amount % 100 < 10 or amount % 100 >= 20):
        return UNIT_FORMS[unit]['few']
    else:
        return UNIT_FORMS[unit]['many']


INGREDIENT_FORMAT = "{idx}. {name} - {total_amount} {unit}"
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
                unit=get_correct_unit_form(item['total_amount'], item['unit'])
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
