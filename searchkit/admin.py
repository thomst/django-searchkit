from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Search
from .forms import SearchForm
from .filters import SearchkitFilter


@admin.register(Search)
class SearchkitSearchAdmin(admin.ModelAdmin):
    form = SearchForm
    list_display = ('name', 'contenttype', 'created_date')

    def get_url_for_applied_search(self, obj):
        app_label = obj.contenttype.app_label
        model_name = obj.contenttype.model
        base_url = reverse(f'admin:{app_label}_{model_name}_changelist')
        return f'{base_url}?{SearchkitFilter.parameter_name}={obj.pk}'

    def response_add(self, request, obj, *args, **kwargs):
        if '_save_and_apply' in request.POST:
            return HttpResponseRedirect(self.get_url_for_applied_search(obj))
        else:
            return super().response_add(request, obj, *args, **kwargs)

    def response_change(self, request, obj, *args, **kwargs):
        if '_save_and_apply' in request.POST:
            return HttpResponseRedirect(self.get_url_for_applied_search(obj))
        else:
            return super().response_change(request, obj, *args, **kwargs)
