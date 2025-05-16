from functools import wraps
from django import forms
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.apps import apps
from django.views.generic import View
from .searchkit import SearchkitForm


def require_ajax(view):
    @wraps(view)
    def _wrapped_view(request, *args, **kwargs):
        if request.is_ajax():
            return view(request, *args, **kwargs)
        else:
            raise PermissionDenied()
    return _wrapped_view


# TODO: What about security? Permission? Authentication?
class SearchkitAjaxView(View):
    """
    Return a searchkit view to update the formset via ajax.
    """
    @require_ajax
    def get(self, request, app_label, model_name, index):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        form = SearchkitForm(model, index, data=request.GET)
        if form.is_valid():
            form.extend()
        return HttpResponse(form.as_div())


class SearchkitView(View):

    def post(self, request, app_label, model_name):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        data = request.POST.copy()
        indices = data['index']
        for index in indices:
            data['index'] = index
            form = SearchkitForm(model, data)
