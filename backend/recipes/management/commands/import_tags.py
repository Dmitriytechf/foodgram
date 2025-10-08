from recipes.models import Tag
from management.utils.base_import_command import BaseImportCommand


class Command(BaseImportCommand):
    """Загрузка данных из tags.json"""

    file_path = '/app/data/tags.json'
    model = Tag
