from django.contrib import admin
from .models import Category, Language, Location, HeritageRecord

admin.site.register(Category)
admin.site.register(Language)
admin.site.register(Location)
admin.site.register(HeritageRecord)