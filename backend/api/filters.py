from django_filters import rest_framework as filters

from recipes.models import Favorite, ShoppingList, Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')


class RecipetFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name="author", lookup_expr='exact')
    tags = filters.CharFilter(method='filter_tags')
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_tags(self, queryset, name, value):
        if not value:
            return queryset
        tags = [tag_value for tag_value in self.request.GET.getlist('tags')]
        queryset = queryset.filter(tags__slug__in=tags)

        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return Favorite.objects.none()
        favorites = Favorite.objects.filter(user=self.request.user)
        return queryset.filter(
            id__in=[recipe.recipes_id for recipe in favorites]
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return ShoppingList.objects.none()
        shopping_cart = ShoppingList.objects.filter(user=self.request.user)
        return queryset.filter(
            id__in=[recipe.recipes_id for recipe in shopping_cart]
        )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
