from django.contrib import admin
from .models import ThreeDGeneration


@admin.register(ThreeDGeneration)
class ThreeDGenerationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'status',
        'meshy_task_id',
        'created_at',
        'updated_at',
    ]

    list_filter = [
        'status',
        'created_at',
    ]

    search_fields = [
        'meshy_task_id',
    ]

    readonly_fields = [
        'id',
        'meshy_task_id',
        'status',
        'model_url',
        'error_message',
        'created_at',
        'updated_at',
    ]