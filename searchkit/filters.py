from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from .models import Search
from .utils import is_searchable_model


class SearchkitFilter(admin.SimpleListFilter):
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
            # We use distinct since we might filter over many-to-many relations.
            return queryset.filter(search.as_q()).distinct()
        else:
            return queryset


class SearchableModelFilter(admin.filters.RelatedFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        contenttypes = ContentType.objects.order_by('app_label', 'model')
        self.lookup_choices = [(m.id, m) for m in contenttypes if is_searchable_model(m.model_class())]
