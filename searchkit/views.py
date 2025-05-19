from django.http import HttpResponse
from django.apps import apps
from django.views.generic import View
from .searchkit import SearchkitFormSet


# TODO: What about security? Permission? Authentication?
class SearchkitAjaxView(View):
    """
    Dynamically reload the formset.
    """
    def get(self, request, app_label, model_name):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        formset = SearchkitFormSet(model, data=request.GET)
        return HttpResponse(formset.render())


# class SearchkitView(View):

#     def post(self, request, app_label, model_name):
#         model = apps.get_model(app_label=app_label, model_name=model_name)
#         data = request.POST.copy()
#         indices = data['index']
#         for index in indices:
#             data['index'] = index
#             form = SearchkitForm(model, data)
