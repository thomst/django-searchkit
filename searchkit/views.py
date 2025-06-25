from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.http import Http404, HttpResponseBadRequest
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.views.generic import View
from .forms import SearchkitModelForm
from .forms import searchkit_formset_factory


# FIXME: Check permissions and authentication.
class SearchkitAjaxView(View):
    """
    Reload the formset via ajax.
    """
    def get(self, request, **kwargs):
        model_form = SearchkitModelForm(data=self.request.GET)
        if model_form.is_valid():
            model = model_form.cleaned_data['searchkit_model'].model_class()
            formset = searchkit_formset_factory(model=model)(data=request.GET)
            return HttpResponse(formset.render())
        else:
            return HttpResponseBadRequest(_('Invalid searchkit-model-form.'))
