from recipes.models import Ingredient
from management.utils.base_import_command import BaseImportCommand


class Command(BaseImportCommand):
    """Загрузка данных из ingredients.json"""

    file_path = '/app/data/ingredients.json'
    model = Ingredient
