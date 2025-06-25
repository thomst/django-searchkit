from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType
from .models import Search


class SearchkitFilter(SimpleListFilter):
    title = 'Searchkit Filter'
    parameter_name = 'search'
    template = 'searchkit/searchkit_filter.html'

    def __init__(self, request, params, model, model_admin):
        # We need the app_label and model as get parameter for the new search
        # link.
        self.searchkit_model = ContentType.objects.get_for_model(model)
        super().__init__(request, params, model, model_admin)

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        searches = Search.objects.filter(contenttype=self.searchkit_model).order_by('-created_date')
        return [(str(obj.id), obj.name) for obj in searches]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected SearchkitSearch object
        if self.value():
            search = Search.objects.get(id=int(self.value()))
            return queryset.filter(**search.as_lookups())
