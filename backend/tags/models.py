from django.db import models


class Tag(models.Model):
    """Модель тегов для рецептов"""
    name = models.CharField(
        max_length=32,
        unique=True
    )
    slug = models.SlugField(
        max_length=32,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name
