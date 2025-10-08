import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка данных с файла ingredients.json"""

    def handle(self, *args, **options):
        # Путь к файлу в контейнере
        file_path = '/app/data/ingredients.json'

        self.stdout.write(f"Пытаемся открыть файл: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ingredients_to_create = [
                    Ingredient(
                        name=item['name'].strip(),
                        measurement_unit=item['measurement_unit'].strip()
                    )
                    for item in data
                ]

                # Один вызов для создания всех записей
                Ingredient.objects.bulk_create(
                    ingredients_to_create,
                    ignore_conflicts=True
                )

            self.stdout.write(self.style.SUCCESS(
                f'Импорт из ingredients.json: обработано {len(data)} записей, '
                f'добавлено в базу {len(ingredients_to_create)} ингредиентов'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при загрузке файла {file_path}: {e}'
            ))
