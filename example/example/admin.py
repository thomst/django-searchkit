from django.contrib import admin
from searchkit.actions import searchkit_action
from searchkit.filters import SearchkitFilter
from .models import ModelA
from .models import ModelB


@admin.register(ModelA)
class ModelAAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ModelA._meta.fields]
    actions = [searchkit_action]
    list_filter = [SearchkitFilter]


@admin.register(ModelB)
class ModelBAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ModelB._meta.fields]
    actions = [searchkit_action]
    list_filter = [SearchkitFilter]
