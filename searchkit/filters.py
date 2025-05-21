from django.contrib.admin import SimpleListFilter
from searchkit.models import SearchkitSearch
from searchkit.searchkit import SearchkitFormSet


class SearchkitFilter(SimpleListFilter):
    title = 'Searchkit Filter'
    parameter_name = 'search'
    template = 'searchkit/filters/filter.html'

    def lookups(self, request, model_admin):
        # Fetch the last three objects from SearchkitSearch and return them as
        # choices.
        searches = SearchkitSearch.objects.all().order_by('-created_date')[:3]
        return [(str(obj.id), obj.name) for obj in searches]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected SearchkitSearch object
        if self.value():
            search = SearchkitSearch.objects.get(id=int(self.value()))
            formset = SearchkitFormSet(search.contenttype.model_class(), search.data)

            if formset.is_valid():  # Hopefully we only saved valid searches.
                # Apply the filters from the formset to the queryset
                return queryset.filter(**formset.get_filter_rules())
