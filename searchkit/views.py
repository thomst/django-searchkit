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
class SearchkitAjaxView(View):
    """
    Reload the formset via ajax.
    """
    def get_model(self, **kwargs):
        """
        Get the model from the URL parameters.
        """
        if all(k in kwargs for k in ('app_label', 'model_name')):
            app_label, model_name = kwargs['app_label'], kwargs['model_name']
            try:
                return apps.get_model(app_label=app_label, model_name=model_name)
            except LookupError:
                raise Http404(f'Model {app_label}.{model_name} not found')
        else:
            return None

    def get(self, request, **kwargs):
        model = self.get_model(**kwargs)
        formset = SearchkitFormSet(data=request.GET, model=model)
        return HttpResponse(formset.render())
