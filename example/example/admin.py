from django.contrib import admin
from searchkit.filters import SearchkitFilter
from .models import ModelA
from .models import ModelB


@admin.register(ModelA)
class ModelAAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ModelA._meta.fields]
    list_filter = [SearchkitFilter]


@admin.register(ModelB)
class ModelBAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ModelB._meta.fields]
    list_filter = [SearchkitFilter]
