from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType
from .models import SearchkitSearch


class SearchkitFilter(SimpleListFilter):
    title = 'Searchkit Filter'
    parameter_name = 'search'
    template = 'searchkit/searchkit_filter.html'

    def __init__(self, request, params, model, model_admin):
        # We need the app_label and model_name for the reverse url lookup in the
        # template.
        self.app_label = model._meta.app_label
        self.model_name = model._meta.model_name
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        # Fetch the last three objects from SearchkitSearch and return them as
        # choices.
        ct = ContentType.objects.get_for_model(model_admin.model)
        searches = SearchkitSearch.objects.filter(contenttype=ct).order_by('-created_date')[:3]
        return [(str(obj.id), obj.name) for obj in searches]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected SearchkitSearch object
        if self.value():
            search = SearchkitSearch.objects.get(id=int(self.value()))
            return queryset.filter(**search.get_filter_rules())
