from django.contrib import admin
from .models import SearchkitSearch
from .forms import SearchkitSearchForm


@admin.register(SearchkitSearch)
class SearchkitSearchAdmin(admin.ModelAdmin):
    form = SearchkitSearchForm
    list_display = ('name', 'contenttype', 'created_date')
