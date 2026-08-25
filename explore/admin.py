from django.contrib import admin
from .models import ExplorePlace, ExploreEra


@admin.register(ExplorePlace)
class ExplorePlaceAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'district',
        'display_order',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'district',
    ]

    search_fields = [
        'name',
        'district',
        'short_description',
    ]

    ordering = [
        'display_order',
    ]


@admin.register(ExploreEra)
class ExploreEraAdmin(admin.ModelAdmin):
    list_display = [
        'place',
        'era_name',
        'year',
        'order',
    ]

    search_fields = [
        'place__name',
        'era_name',
        'description',
    ]

    ordering = [
        'place',
        'order',
    ]