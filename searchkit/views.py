from datetime import datetime
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.http import Http404
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from django.views.generic import View
from django.views.generic import FormView
from django.views.generic import CreateView
from .models import SearchkitSearch
from .forms import SearchkitSearchForm
from .searchkit import SearchkitFormSet


# FIXME: Check permissions and authentication.

class GetModelMixin:
    """
    Mixin to get the model from the URL parameters.
    """
    def get_model(self, **kwargs):
        """
        Get the model from the URL parameters.
        """
        kwargs = kwargs or self.kwargs
        app_label = kwargs['app_label']
        model_name = kwargs['model_name']
        try:
            return apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError:
            raise Http404(f'Model {app_label}.{model_name} not found')

    @cached_property
    def model(self):
        return self.get_model()


class SearchkitAjaxView(GetModelMixin, View):
    """
    Reload the formset via ajax.
    """
    def get(self, request, **kwargs):
        formset = SearchkitFormSet(self.model, data=request.GET)
        return HttpResponse(formset.render())


# TODO: Is it even possible to use generic views for ModelForms here?
class SearchkitFilterView(GetModelMixin, FormView):
    template_name = 'searchkit/filters/form.html'
    form_class = SearchkitSearchForm

    def get_form_kwargs(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial']['name'] = f'Search for {self.model._meta.verbose_name} ({now})'
        kwargs['initial']['contenttype'] = ContentType.objects.get_for_model(self.model)
        return kwargs

    def form_valid(self, form):
        # Save search data.
        search = SearchkitSearch(
            name=form.cleaned_data['name'],
            contenttype=form.cleaned_data['contenttype'],
            data=form.cleaned_data['data'],
        )
        search.save()

        # Redirect back to the change list with the search applied.
        change_list_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
        return HttpResponseRedirect(f'{change_list_url}?search={search.id}')
