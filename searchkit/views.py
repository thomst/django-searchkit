from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.shortcuts import render
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.views.generic import View
from django.views.generic import FormView
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


class SearchkitFilterView(FormView):
    template_name = 'searchkit/filters/form.html'
    form_class = SearchkitSearchForm

    def get_model(self):
        """
        Get the model from the URL parameters.
        """
        app_label = self.kwargs['app_label']
        model_name = self.kwargs['model_name']
        try:
            return apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError:
            # FIXME: Use specific exception.
            raise Exception(f'Model {app_label}.{model_name} not found')

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        kwargs['model'] = self.get_model()
        return kwargs

    def form_valid(self, form):
        # Save search data.
        model = self.get_model()
        search = SearchkitSearch(
            name=form.cleaned_data['name'],
            contenttype=ContentType.objects.get_for_model(model),
            data=form.cleaned_data['data'],
        )
        search.save()

        # Redirect back to the change list with the search applied.
        change_list_url = reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist')
        return HttpResponseRedirect(f'{change_list_url}?search={search.id}')
