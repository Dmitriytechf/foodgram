from django.urls import path

from . import views

app_name = 'recipes'

urlpatterns = [
    path('<int:pk>/', views.recipe_short_link, name='recipe-short-link'),
]
