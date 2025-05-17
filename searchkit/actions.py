from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from .searchkit import SearchkitFormSet
from .forms import SearchkitSearchForm
from .models import SearchkitSearch
from .tests import TEST_DATA


def searchkit_action(modeladmin, request, queryset):
    """
    A base admin action that displays an intermediate page with a form.
    """
    if 'searchkit_action' in request.POST:
        # Handle form submission
        search_form = SearchkitSearchForm(request.POST)
        formset = SearchkitFormSet(modeladmin.model, request.POST)

        if search_form.is_valid() and formset.is_valid():

            # Save search data.
            search = SearchkitSearch(
                name=search_form.cleaned_data['name'],
                contenttype=ContentType.objects.get_for_model(modeladmin.model),
                data=formset.data
            )
            search.save()

            # Redirect back to the change list with the search applied.
            model_name = modeladmin.model._meta.model_name
            app_label = modeladmin.model._meta.app_label
            change_list_url = reverse(f'admin:{app_label}_{model_name}_changelist')
            return HttpResponseRedirect(f'{change_list_url}?search={search.id}')

    else:
        # Display the form
        search_form = SearchkitSearchForm()
        formset = SearchkitFormSet(modeladmin.model, data=TEST_DATA)

        return render(request, 'admin/searchkit/searchkit_action.html', {
            'objects': queryset.order_by('pk'),
            'search_form': search_form,
            'formset': formset,
        })

searchkit_action.short_description = "Save and apply a searchkit search."
