from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .validators import cooking_time_validator
from recipes.models import (
    User,
    Recipe,
    Tag,
    Ingredient,
    Subscription,
    Favorite,
    ShoppingList,
    IngredientAmount,
)


class CreatetUserSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name',
            'last_name', 'password'
        ]
        required_fields = ['username', 'first_name', 'last_name']


class UserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return getattr(obj, 'is_subscribed', False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'password', 'is_subscribed'
        ]
        required_fields = ['username', 'first_name', 'last_name']


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    def validate_avatar(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Empty request')
        return attrs

    def update(self, instance, validated_data):
        avatar_data = validated_data.get('avatar', None)
        file = ContentFile(avatar_data.read())
        instance.avatar.save('image.png', file, save=True)
        return instance

    class Meta:
        model = User
        fields = [
            'avatar'
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']
        read_only_fields = ['id']
        extra_kwargs = {'measurement_unit': {'read_only': True}}


class IngredientAmountSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = IngredientAmount
        fields = ['ingredient', 'amount']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        formatted_ingredient = data['ingredient']
        formatted_ingredient['amount'] = data['amount']
        return formatted_ingredient


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    def get_ingredients(self, obj):
        return IngredientAmountSerializer(
            IngredientAmount.objects.filter(recipe=obj), many=True
        ).data

    class Meta:
        model = Recipe
        exclude = ['short_link', 'pub_date']


class RecipeWriteSerializer(RecipeGetSerializer):
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        required=True,
        validators=[cooking_time_validator]
    )

    def validate(self, data):
        data = super().validate(data)
        request = self.context['request']
        tags_data = request.data.get('tags')
        ingredients_data = request.data.get('ingredients')
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': ['Обязательное поле.']}
            )
        unique_ingredients = set()
        new_ingredients_data = []
        for ingredient_data in ingredients_data:
            if not ingredient_data.get('amount'):
                raise serializers.ValidationError(
                    {'amount': ['Обязательное поле.']}
                )
            if not ingredient_data.get('id'):
                raise serializers.ValidationError(
                    {'id': ['Обязательное поле.']}
                )
            if ingredient_data['id'] in unique_ingredients:
                raise serializers.ValidationError(
                    {'ingredients': ['Повторяющееся значение.']}
                )
            try:
                if int(ingredient_data.get('amount')) <= 0:
                    raise serializers.ValidationError(
                        {'amount': ['Должно быть больше 0.']}
                    )
            except ValueError:
                raise serializers.ValidationError(
                    {'amount': ['Значение должно быть целым числом.']}
                )
            unique_ingredients.add(ingredient_data['id'])
        try:
            ingredients = Ingredient.objects.filter(id__in=unique_ingredients)
            for ingredient in ingredients_data:
                new_ingredients_data.append(
                    {
                        'ingredient': ingredients.get(pk=ingredient['id']),
                        'amount': ingredient['amount']
                    }
                )
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                {'ingredients': ['Несуществующий ингредиент.']}
            )
        new_tags_data = []
        if not tags_data:
            raise serializers.ValidationError(
                {'tags': ['Обязательное поле.']}
            )
        for tag_data in tags_data:
            try:
                tag = Tag.objects.get(pk=tag_data)
                if tag in new_tags_data:
                    raise serializers.ValidationError(
                        {'tags': ['Повторяющееся значение.']}
                    )
                else:
                    new_tags_data.append(tag)
            except Tag.DoesNotExist:
                raise serializers.ValidationError(
                    {'Tag': ['Несуществующий тег.']}
                )
        data['ingredients'] = new_ingredients_data
        data['tags'] = new_tags_data
        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                {'image': 'Обязательное поле.'}
            )
        return value

    def create_ingredients(self, data, recipe):
        ingredients_data = [
            {
                'ingredient': ingredient_data['ingredient'],
                'amount': ingredient_data['amount']
            } for ingredient_data in data
        ]
        IngredientAmount.objects.bulk_create(
            [
                IngredientAmount(
                    recipe=recipe, **ingredient_data
                ) for ingredient_data in ingredients_data
            ],
        )

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('is_favorited')
        validated_data.pop('is_in_shopping_cart')
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.set(validated_data.pop('tags'))
        self.create_ingredients(validated_data.pop('ingredients'), instance)
        return super().update(instance, validated_data)


class UserWithRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = Base64ImageField()
    is_subscribed = serializers.BooleanField(default=False)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None
        )
        if recipes_limit:
            recipes = Recipe.objects.filter(
                author=obj
            )[:int(recipes_limit)]
        else:
            recipes = Recipe.objects.filter(author=obj)
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    class Meta:
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    subscriber = UserSerializer(read_only=True)

    def validate(self, data):
        request = self.context['request']
        try:
            subscriber = User.objects.get(
                pk=self.context['view'].kwargs.get('id')
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'subscriber': ['Пользователь не найден.']}
            )
        if request.user == subscriber:
            raise serializers.ValidationError(
                {'subscriber': ['Нельзя подписаться на самого себя.']}
            )
        if (
            request.method == 'POST' and Subscription.objects.filter(
                user=request.user,
                subscriber=subscriber
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    'non_field_errors': [
                        'Вы уже подписаны на этого пользователя.'
                    ]
                }
            )
        return data

    def to_representation(self, instance):
        return UserWithRecipeSerializer(
            instance.subscriber, context=self.context
        ).data

    class Meta:
        model = Subscription
        fields = [
            'subscriber'
        ]
        read_only_fields = ['user', 'subscriber']


class ShortRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'image', 'cooking_time'
        ]


class ShoppingListSerializer(serializers.ModelSerializer):
    recipes = RecipeGetSerializer(read_only=True)

    def validate(self, data):
        request = self.context['request']
        try:
            recipes = Recipe.objects.get(
                pk=self.context['view'].kwargs.get('pk')
            )
        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                {'recipes': ['Recipe does not exist']}
            )
        if (
            request.method == 'POST' and ShoppingList.objects.filter(
                user=request.user,
                recipes=recipes
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    'recipes': [
                        'Recipe is already in a shopping cart'
                    ]
                }
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipes, context=self.context
        ).data

    class Meta:
        model = ShoppingList
        fields = ['recipes']
        read_only_fields = ['user', 'recipes']


class FavoriteSerializer(ShoppingListSerializer):

    def validate(self, data):
        request = self.context['request']
        try:
            recipes = Recipe.objects.get(
                pk=self.context['view'].kwargs.get('pk')
            )
        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                {'recipes': ['Recipe does not exist']}
            )
        if (
            request.method == 'POST' and Favorite.objects.filter(
                user=request.user,
                recipes=recipes
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    'recipes': [
                        'Recipe is already favorited'
                    ]
                }
            )
        return data

    class Meta:
        model = Favorite
        fields = ['recipes']
        read_only_fields = ['user', 'recipes']
