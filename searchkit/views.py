from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from .forms import SearchkitModelForm
from .forms import searchkit_formset_factory


class InvalidModelFormException(APIException):
    status_code = 400
    default_detail = _('Invalid searchkit model form.')
    default_code = 'invalid_model_form'


class SearchkitPermission(BasePermission):
    def has_permission(self, request, view):
        # Allow access only if the user has the 'add' or 'change' permissions.
        return (
            request.user.has_perm('searchkit.add_search')
            or request.user.has_perm('searchkit.change_search')
        )


class SearchkitView(APIView):
    """
    Update the searchkit formset via ajax.
    """
    permission_classes = [SearchkitPermission]

    def get(self, request, **kwargs):
        model_form = SearchkitModelForm(data=self.request.GET)
        if model_form.is_valid():
            model = model_form.cleaned_data['searchkit_model'].model_class()
            formset = searchkit_formset_factory(model=model)(data=request.GET)
            return Response(formset.render())
        else:
            raise InvalidModelFormException()
