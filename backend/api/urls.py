from django.urls import include, path

urlpatterns = [
    path('', include('users.urls')),
    path('recipes/', include('recipes.urls')),
    path('ingredients/', include('ingredients.urls')),
    path('tags/', include('tags.urls')),
]
