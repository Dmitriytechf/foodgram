import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet,
                                           BooleanFilter, CharFilter)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.http import Http404
from django.http import FileResponse
from django.urls import reverse

from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Subscription, Tag)
from .permission import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, TagSerializer,
                          UserWithRecipesSerializer)
from .shopping_list_utils import generate_shopping_list_content


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для тегов.
    Только чтение (list и retrieve).
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientFilter(FilterSet):
    """
    Вьюсет для фильтрации ингредиентов.
    """
    name = CharFilter(field_name='name', lookup_expr='istartswith')
    search = CharFilter(field_name='name', lookup_expr='istartswith')
    q = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для ингредиентов.
    Только чтение с поиском по имени.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeFilter(FilterSet):
    """Фильтр для рецептов"""
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    tags = CharFilter(method='filter_tags_by_slug')

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset

    def filter_tags_by_slug(self, queryset, name, value):
        if value:
            tag_slugs = self.request.query_params.getlist('tags')
            if tag_slugs:
                return queryset.filter(tags__slug__in=tag_slugs).distinct()
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов со всеми эндпоинтами из ТЗ"""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Автоматически устанавливаем автора при создании"""
        serializer.save(author=self.request.user)

    def _handle_recipe_action(self, request, pk, model_class):
        """Общий метод для добавления/удаления рецепта в избранное/корзину"""
        if request.method == 'DELETE':
            item = get_object_or_404(
                model_class,
                user=request.user,
                recipe_id=pk
            )
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, id=pk)
        _, created = model_class.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже добавлен в '
                f'{model_class._meta.verbose_name}'
            )

        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное"""
        return self._handle_recipe_action(
            request, pk, Favorite
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок"""
        return self._handle_recipe_action(
            request, pk, ShoppingCart
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок"""
        ingredients = IngredientAmount.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')

        recipes = Recipe.objects.filter(
            shoppingcart__user=request.user
        ).distinct().order_by('name')

        file_content = generate_shopping_list_content(ingredients, recipes)

        return FileResponse(
            file_content,
            as_attachment=True,
            filename='foodgram_shopping_list.txt',
            content_type='text/plain'
        )

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Короткая ссылка на рецепт"""
        if not Recipe.objects.filter(id=pk).exists():
            raise Http404(f'Рецепт с id {pk} не найден')

        return Response({
            'short-link': request.build_absolute_uri(
                reverse('recipes:recipe-short-link', kwargs={'pk': pk})
            )
        })


class UserFoodgramViewSet(UserViewSet):
    """Кастомный вьюсет пользователя с дополнительными полями"""

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Список моих подписок"""
        user = request.user
        subscriptions = User.objects.filter(
            followings__user=user
        )

        # Пагинация
        page = self.paginate_queryset(subscriptions)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписаться/отписаться на пользователя"""
        user = request.user

        if request.method == 'DELETE':
            # Для удаления используем только ID автора
            subscription = get_object_or_404(
                Subscription,
                user=user,
                author_id=id
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = self.get_object()

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')

        _, created = Subscription.objects.get_or_create(
            user=user,
            author=author
        )

        if not created:
            raise serializers.ValidationError(
                f'Вы уже подписаны на пользователя {author.username}'
            )

        serializer = UserWithRecipesSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        url_name='me-avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, JSONParser]
    )
    def avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method == 'PUT':
            avatar_file = None
            if 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']

            elif 'avatar' in request.data:
                avatar_data = request.data['avatar']

                if (isinstance(avatar_data, str)
                        and avatar_data.startswith('data:image')):
                    try:
                        format, imgstr = avatar_data.split(';base64,')
                        ext = format.split('/')[-1]
                        filename = f"{uuid.uuid4()}.{ext}"
                        avatar_file = ContentFile(
                            base64.b64decode(imgstr),
                            name=filename
                        )
                    except Exception:
                        return Response(
                            {'error': 'Invalid image format'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            if not avatar_file:
                return Response(
                    {'error': 'Avatar file is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.avatar = avatar_file
            user.save()

            avatar_url = request.build_absolute_uri(user.avatar.url)

            return Response(
                {'avatar': avatar_url},
                status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
