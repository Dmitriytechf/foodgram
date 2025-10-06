import base64
import io
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Ingredient, Tag, Recipe, IngredientAmount,
                            Favorite, ShoppingCart)
from users.models import Profile, Subscription

from .permission import IsAuthorOrReadOnly
from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          UserWithRecipesSerializer, )


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для тегов.
    Только чтение (list и retrieve).
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для ингредиентов.
    Только чтение с поиском по имени.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('^name',)


class RecipeFilter:
    """Фильтр для рецептов"""
    @staticmethod
    def filter_recipes(queryset, request):
        # Фильтрация по автору
        author_id = request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Фильтрация по избранному
        is_favorited = request.query_params.get('is_favorited')
        if is_favorited == '1' and request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=request.user)

        # Фильтрация по списку покупок
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and request.user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=request.user)

        # Фильтрация по тегам
        tags = request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов со всеми эндпоинтами из ТЗ"""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Автоматически устанавливаем автора при создании"""
        serializer.save(author=self.request.user)

    def _handle_recipe_action(self, request, pk, model_class, error_message):
        """Общий метод для добавления/удаления рецепта в избранное/корзину"""
        if request.method == 'DELETE':
            item = get_object_or_404(
                model_class,
                user=request.user,
                recipe_id=pk
            )
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # POST метод
        recipe = self.get_object()

        if model_class.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(error_message)

        model_class.objects.create(user=request.user, recipe=recipe)
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
            request, pk, Favorite, 'Рецепт уже в избранном'
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок"""
        return self._handle_recipe_action(
            request, pk, ShoppingCart, 'Рецепт уже в списке покупок'
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок"""
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')

        shopping_list = []
        shopping_list.append("Foodgram - Список покупок")
        shopping_list.append("-" * 50)
        shopping_list.append("")

        for idx, item in enumerate(ingredients, 1):
            shopping_list.append(
                f"{idx:2d}. {item['name']:<25} "
                + f"{item['total_amount']:>5} {item['unit']}"
            )

        shopping_list.append("")
        shopping_list.append("-" * 50)
        shopping_list.append(f"Всего ингредиентов: {len(ingredients)}")
        shopping_list.append("-" * 50)

        file_content = "\n".join(shopping_list)

        buffer = io.BytesIO(file_content.encode('utf-8'))

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='foodgram_shopping_list.txt'
        )

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Короткая ссылка на рецепт"""
        recipe = self.get_object()
        short_link = f"https://foodgram.example.org/recipes/{recipe.id}/"
        return Response({'short-link': short_link})


class UserViewSet(UserViewSet):
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
            following__user=user).order_by('-following__created_at')

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
                author_id=id  # используем id вместо объекта author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = self.get_object()

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')

        Subscription.objects.create(user=user, author=author)
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
        self.get_object = lambda: request.user
        return self.retrieve(request, *args, **kwargs)

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

            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                user.refresh_from_db()

            user.profile.avatar = avatar_file
            user.profile.save()

            avatar_url = request.build_absolute_uri(user.profile.avatar.url)

            return Response(
                {'avatar': avatar_url},
                status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            if hasattr(user, 'profile') and user.profile.avatar:
                user.profile.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
