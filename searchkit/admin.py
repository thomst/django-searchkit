from django.contrib import admin
from .models import SearchkitSearch


@admin.register(SearchkitSearch)
class SearchkitSearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_date')
