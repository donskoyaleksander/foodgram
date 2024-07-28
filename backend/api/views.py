
import io
import csv

from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from api.filters import IngredientFilter, RecipetFilter
from api.paginations import NoPagination
from api.permissions import RecipePermission
from api.serializers import (
    UserSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    SubscriptionSerializer,
    ShoppingListSerializer,
    RecipeSerializer,
    AvatarSerializer,
)
from recipes.models import (
    Recipe,
    User,
    Tag,
    Ingredient,
    Favorite,
    ShoppingList,
    Subscription,
)


DOMAIN = '127.0.0.1:8000'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pk_url_kwarg = 'pk'
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            subscribers = Subscription.objects.filter(
                subscriber=OuterRef('pk'), user=user
            )
            return super().get_queryset().annotate(
                is_subscribed=Exists(subscribers)
            )
        return super().get_queryset()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.request.user
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request, *args, **kwargs):
        user = self.request.user
        if user.avatar:
            user.avatar.delete()
        serializer = AvatarSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"avatar": user.avatar.url})

    @avatar.mapping.delete
    def delete_avater(self, request, *args, **kwargs):
        user = self.request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            user.update_password(
                new_password=request.data.get('new_password'),
                old_password=request.data.get('current_password')
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request, *args, **kwargs):
        users = self.request.user.respondent.all()
        page = self.paginate_queryset(users)
        serializer = self.get_serializer(page, many=True)
        serializer = self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, *args, **kwargs):
        user = self.request.user
        subscriber = get_object_or_404(User, pk=self.kwargs[self.pk_url_kwarg])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            user=user,
            subscriber=subscriber
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @subscribe.mapping.delete
    def unsubscride(self, request, *args, **kwargs):
        user = self.request.user
        subscriber = get_object_or_404(User, pk=self.kwargs[self.pk_url_kwarg])
        if Subscription.objects.filter(
            user=user, subscriber=subscriber
        ).exists():
            Subscription.objects.filter(
                user=user, subscriber=subscriber
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ['subscriptions', 'subscribe']:
            return SubscriptionSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'create':
            context['exclude_fields'] = [
                'is_subscribed', 'avatar'
            ]
        return context


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = NoPagination


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = NoPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


def get_shopping_list(user):
    shopping_list = ShoppingList.objects.filter(user=user)
    ingredient_counts = {}
    response = io.StringIO()
    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Amount'])
    for recipe in shopping_list:
        ingredients = recipe.recipes.ingredients.all()
        for ingredient in ingredients:
            ingredient_amount = ingredient.ingredientamount_set.first()
            if ingredient_amount.ingredient.name in ingredient_counts:
                ingredient_counts[
                    ingredient_amount.ingredient.name
                ] += ingredient_amount.amount
            else:
                ingredient_counts[
                    ingredient_amount.ingredient.name
                ] = ingredient_amount.amount
    for key, value in ingredient_counts.items():
        writer.writerow([key, value])
    response.seek(0)
    return response


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related('author', 'ingredients', 'tags')
    serializer_class = RecipeSerializer
    pk_url_kwarg = 'pk'
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipetFilter
    permission_classes = [IsAuthenticatedOrReadOnly, RecipePermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            favorites = Favorite.objects.filter(
                recipes=OuterRef('pk'), user=user
            )
            shopping_cart = ShoppingList.objects.filter(
                recipes=OuterRef('pk'), user=user
            )
            subscribers = Subscription.objects.filter(
                subscriber=OuterRef('author'), user=user
            )
            return super().get_queryset().annotate(
                is_favorite=Exists(favorites),
                is_in_shopping_cart=Exists(shopping_cart),
                is_subscribed=Exists(subscribers)
            )
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def action_base_post(self):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=self.kwargs[self.pk_url_kwarg])
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            user=user,
            recipes=recipe
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def action_base_delete(self, manager):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=self.kwargs[self.pk_url_kwarg])
        if manager.filter(
            user=user, recipes=recipe
        ).exists():
            manager.filter(
                user=user, recipes=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_url = f'https://{DOMAIN}/s/{recipe.short_link}'
        return Response({'short-link': short_url})

    @action(
        methods=['post'],
        detail=True,
    )
    def shopping_cart(self, request, pk=None):
        return self.action_base_post()

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.action_base_delete(ShoppingList.objects)

    @action(
        methods=['get'],
        detail=False,
    )
    def download_shopping_cart(self, request, pk=None):
        shopping_list = get_shopping_list(self.request.user)
        print(shopping_list)
        response = FileResponse(
            iter([shopping_list.getvalue()]), content_type='text/csv'
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_cart.csv"'
        return response

    @action(
        methods=['post'],
        detail=True,
    )
    def favorite(self, request, pk=None):
        return self.action_base_post()

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.action_base_delete(Favorite.objects)

    def get_serializer_class(self):
        if self.action in ['shopping_cart', 'download_shopping_cart']:
            return ShoppingListSerializer
        if self.action == 'favorite':
            return FavoriteSerializer
        return RecipeSerializer
