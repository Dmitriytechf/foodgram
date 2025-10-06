from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register('users', views.UserViewSet, basename='users')

urlpatterns = [
    path('users/subscriptions/',
         views.UserViewSet.as_view({'get': 'subscriptions'}),
         name='subscriptions'),
    path('users/<int:id>/subscribe/',
         views.UserViewSet.as_view({'post': 'subscribe',
                                    'delete': 'subscribe'}),
         name='subscribe'),
    path('users/me/avatar/',
         views.UserViewSet.as_view({'put': 'avatar',
                                    'delete': 'avatar'}),
         name='me-avatar'),
    # Djoser main
    path('', include('djoser.urls')),
    # Token auth
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    path('', include(router.urls)),
]
