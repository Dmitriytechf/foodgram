from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register('users', views.UserFoodgramViewSet, basename='users')

urlpatterns = [
    path('users/subscriptions/',
         views.UserFoodgramViewSet.as_view({'get': 'subscriptions'}),
         name='subscriptions'),
    path('users/<int:id>/subscribe/',
         views.UserFoodgramViewSet.as_view({'post': 'subscribe',
                                            'delete': 'subscribe'}),
         name='subscribe'),
    path('', include('djoser.urls')),
    path('', include(router.urls)),
]
