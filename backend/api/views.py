from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from api.utils import get_shopping_list
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
    RecipeGetSerializer,
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
from foodgram.settings import DOMAIN


class UserViewSet(DjoserUserViewSet):
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    pk_url_kwarg = 'id'
    search_fields = ['username']
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        if user.is_authenticated:
            subscribers = Subscription.objects.filter(
                subscriber=OuterRef('pk'), user=user
            )
            queryset = queryset.annotate(
                is_subscribed=Exists(subscribers)
            )
        return queryset

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request, *args, **kwargs):
        user = self.request.user
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
        subscriber = get_object_or_404(User, pk=kwargs[self.pk_url_kwarg])
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
        subscriber = get_object_or_404(User, pk=kwargs[self.pk_url_kwarg])
        del_count, _ = Subscription.objects.filter(
            user=user, subscriber=subscriber
        ).delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ['subscriptions', 'subscribe']:
            return SubscriptionSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer


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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related('author', 'ingredients', 'tags')
    pk_url_kwarg = 'pk'
    serializer_class = RecipeGetSerializer
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
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return super().get_serializer_class()
