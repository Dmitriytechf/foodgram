import json
from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """Базовый класс для команд импорта данных"""

    file_path = None
    model = None
    success_message = "Импорт завершен успешно"

    def handle(self, *args, **options):
        if not self.file_path or not self.model:
            self.stdout.write(self.style.ERROR(
                'Не указан file_path или model в классе команды'
            ))
            return

        self.stdout.write(f'Пытаемся открыть файл: {self.file_path}')

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                objects_to_create = [
                    self.model(**item)
                    for item in data
                ]

                created_objects = self.model.objects.bulk_create(
                    objects_to_create,
                    ignore_conflicts=True
                )

            self.stdout.write(self.style.SUCCESS(
                f'Импорт из {self.file_path}: обработано {len(data)} записей, '
                f'добавлено в базу {len(created_objects)} объектов'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при загрузке файла {self.file_path}: {e}'
            ))
