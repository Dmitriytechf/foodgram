from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Favorite, IngredientAmount, Recipe, ShoppingCart
from .permission import IsAuthorOrReadOnly
from .serializers import RecipeCreateUpdateSerializer, RecipeSerializer


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

    def get_queryset(self):
        """Применяем фильтры к queryset"""
        queryset = super().get_queryset()
        return RecipeFilter.filter_recipes(queryset, self.request)

    def perform_create(self, serializer):
        """Автоматически устанавливаем автора при создании"""
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Переопределяем create"""
        # Создаем рецепт
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        instance = serializer.instance
        output_serializer = RecipeSerializer(instance, context={'request': request})

        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Переопределяем update"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        output_serializer = RecipeSerializer(instance, context={'request': request})
        return Response(output_serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное"""
        recipe = self.get_object()

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite = get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок"""
        recipe = self.get_object()

        if request.method == 'POST':
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            cart_item = get_object_or_404(
                ShoppingCart,
                user=request.user,
                recipe=recipe
            )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок"""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)

        if not shopping_cart:
            return Response(
                {"error": "Список покупок пуст"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')

        # Формируем список
        shopping_list = []
        shopping_list.append("🍽 Foodgram - Список покупок")
        shopping_list.append("-" * 50)
        shopping_list.append("")

        for idx, item in enumerate(ingredients, 1):
            shopping_list.append(
                f"{idx:2d}. {item['name']:<25} {item['total_amount']:>5} {item['unit']}")

        shopping_list.append("")
        shopping_list.append("-" * 50)
        shopping_list.append(f"Всего ингредиентов: {len(ingredients)}")
        shopping_list.append("-" * 50)

        file_content = "\n".join(shopping_list)

        response = HttpResponse(file_content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="foodgram_shopping_list.txt"'

        return response

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
