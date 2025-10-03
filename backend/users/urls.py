from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('users', views.CustomUserViewSet, basename='users')

urlpatterns = [
    path('users/subscriptions/',
         views.CustomUserViewSet.as_view({'get': 'subscriptions'}),
         name='subscriptions'),
    path('users/<int:id>/subscribe/',
         views.CustomUserViewSet.as_view({'post': 'subscribe',
                                          'delete': 'subscribe'}),
         name='subscribe'),
    path('users/me/avatar/',
         views.CustomUserViewSet.as_view({'put': 'avatar',
                                          'delete': 'avatar'}),
         name='me-avatar'),
    # Djoser main
    path('', include('djoser.urls')),
    # Token auth
    path('auth/token/login/',
         views.CustomTokenCreateView.as_view(), name='login'),
    path('auth/token/logout/',
         views.CustomUserViewSet.as_view({'post': 'logout'}),
         name='logout'),
]
