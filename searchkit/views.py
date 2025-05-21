from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.apps import apps
from django.contrib.contenttypes import ContentType
from django.views.generic import View
from .models import SearchkitSearch
from .forms import SearchkitSearchForm
from .searchkit import SearchkitFormSet


# FIXME: Check permissions and authentication.

class SearchkitAjaxView(View):
    """
    Reload the formset via ajax.
    """
    def get(self, request, app_label, model_name):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        formset = SearchkitFormSet(model, data=request.GET)
        return HttpResponse(formset.render())


class SearchkitFilterView(View):
    """
    Work with the SearchkitFilter.
    """
    def get(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError:
            return HttpResponseNotFound(f'Page not found')

        search_form = SearchkitSearchForm()
        formset = SearchkitFormSet(model)

        return render(request, 'searchkit/filter/form.html', {
            'search_form': search_form,
            'formset': formset,
        })

    def post(self, request, app_label, model_name):
        try:
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError:
            return HttpResponseNotFound(f'Page not found')

        search_form = SearchkitSearchForm(request.POST)
        formset = SearchkitFormSet(model, request.POST)

        if search_form.is_valid() and formset.is_valid():

            # Save search data.
            # We save the raw data which has been validated and can be reuesed
            # to instantiate the formset and retrieve the filter rules.
            search = SearchkitSearch(
                name=search_form.cleaned_data['name'],
                contenttype=ContentType.objects.get_for_model(model),
                data=formset.data,
            )
            search.save()

            # Redirect back to the change list with the search applied.
            change_list_url = reverse(f'admin:{app_label}_{model_name}_changelist')
            return HttpResponseRedirect(f'{change_list_url}?search={search.id}')

        else:
            # If the form is not valid, render the form again with errors.
            return render(request, 'searchkit/filter/form.html', {
                    'search_form': search_form,
                    'formset': formset,
                })
