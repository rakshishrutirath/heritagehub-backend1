from rest_framework import serializers
from .models import ExplorePlace, ExploreEra


class ExploreEraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExploreEra
        fields = [
            'id',
            'era_name',
            'year',
            'image',
            'description',
            'order',
        ]


class ExplorePlaceSerializer(serializers.ModelSerializer):
    # Include all historical eras belonging to this place
    eras = ExploreEraSerializer(many=True, read_only=True)

    class Meta:
        model = ExplorePlace
        fields = [
            'id',
            'name',
            'district',
            'short_description',
            'main_image',

            'culture_title',
            'culture_description',
            'culture_image',

            'food_title',
            'food_description',
            'food_image',

            'story_audio',

            'display_order',
            'is_active',
            'created_at',

            'eras',
        ]
