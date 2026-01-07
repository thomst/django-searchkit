from django.utils.http import urlsafe_base64_encode
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from .models import Search
from .forms import SearchForm
from .filters import SearchkitFilter
from .filters import SearchableModelFilter


@admin.register(Search)
class SearchkitSearchAdmin(admin.ModelAdmin):
    form = SearchForm
    list_display = ('name', 'contenttype', 'created_date', 'apply_search_view')
    list_filter = (('contenttype', SearchableModelFilter),)

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        # We do not want to save the object when just applying the search.
        if not '_apply' in request.POST:
            obj.save()

    def get_apply_search_url(self, obj, data=None):
        app_label = obj.contenttype.app_label
        model_name = obj.contenttype.model
        base_url = reverse(f'admin:{app_label}_{model_name}_changelist')
        if data:
            # Use base64 encoded post data url parameter.
            base64_data = urlsafe_base64_encode(data.urlencode().encode('utf-8'))
            return f'{base_url}?{SearchkitFilter.parameter_name}={base64_data}'
        else:
            return f'{base_url}?{SearchkitFilter.parameter_name}={obj.pk}'

    def response_add(self, request, obj, *args, **kwargs):
        if '_save_and_apply' in request.POST:
            return HttpResponseRedirect(self.get_apply_search_url(obj))
        elif '_apply' in request.POST:
            return HttpResponseRedirect(self.get_apply_search_url(obj, request.POST))
        else:
            return super().response_add(request, obj, *args, **kwargs)

    def response_change(self, request, obj, *args, **kwargs):
        if '_save_and_apply' in request.POST:
            return HttpResponseRedirect(self.get_apply_search_url(obj))
        elif '_apply' in request.POST:
            return HttpResponseRedirect(self.get_apply_search_url(obj, data=request.POST))
        else:
            return super().response_change(request, obj, *args, **kwargs)

    def apply_search_view(self, obj):
        """
        Returns a link to apply the search.
        """
        return format_html(
            '<a href="{}" >Apply search "{}"</a>',
            self.get_apply_search_url(obj),
            obj.name
        )
    apply_search_view.short_description = 'Apply Search'
