import csv
import os

from django.core.management.base import BaseCommand
from ingredients.models import Ingredient


class Command(BaseCommand):
    """Загрузка данных с файла ingredients.csv"""

    def handle(self, *args, **options):
        # Путь к файлу в контейнере
        file_path = '/app/data/ingredients.csv'

        self.stdout.write(f"Пытаемся открыть файл: {file_path}")

        try:
            # Добавление ингредиентов
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        Ingredient.objects.get_or_create(
                            name=row[0].strip(),
                            measurement_unit=row[1].strip()
                        )
                        self.stdout.write(f"Добавлен ингредиент: {row[0]}")

            self.stdout.write(self.style.SUCCESS(
                'Ингредиенты успешно загружены!'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            # Проверим что есть в папке /app/data
            if os.path.exists('/app/data'):
                files = os.listdir('/app/data')
                self.stdout.write(f"Файлы в /app/data: {files}")
