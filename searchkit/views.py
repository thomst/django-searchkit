from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.renderers import StaticHTMLRenderer
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import PermissionDenied
from .forms import SearchkitModelForm
from .forms import searchkit_formset_factory


class InvalidSearchkitModel(APIException):
    status_code = 400
    default_detail = _('Invalid searchkit model.')
    default_code = 'invalid_searchkit_model'


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
    renderer_classes = [StaticHTMLRenderer]

    def get(self, request, **kwargs):

        model_form = SearchkitModelForm(data=request.GET)
        if model_form.is_valid():
            model = model_form.cleaned_data['searchkit_model'].model_class()
        else:
            raise InvalidSearchkitModel(model_form.errors)

        formset = searchkit_formset_factory(model=model)(data=request.GET)
        # We reset all errors of the forms since this is no submission but a
        # reload. (Errors are unavoidable when rebuilding the operator field.)
        for form in formset.forms:
            form._errors = dict()
        return Response(formset.render())


class AutocompleteView(APIView):
    """
    Autocomplete view for select2 value fields.
    """
    permission_classes = [SearchkitPermission]
    renderer_classes = [JSONRenderer]
    paginate_by = 25

    def get(self, request, **kwargs):
        try:
            app_label = request.GET['sk_autocomplete_app_label']
            model_name = request.GET['sk_autocomplete_model_name']
            field_name = request.GET['sk_autocomplete_field_name']
        except KeyError as e:
            raise PermissionDenied from e

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError as e:
            raise PermissionDenied from e

        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist as e:
            raise PermissionDenied from e

        perm = f'{app_label}.view_{model_name}'
        if not request.user.has_perm(perm):
            msg = f"User {request.user} is not allowed to view {model_name}"
            raise PermissionDenied(msg)

        # We use distinct together with an order by the field in question. This
        # neutralizes all former order_by clauses which might add columns to the
        # sql distinct statement. See the django docs for more details.
        queryset = model.objects.values_list(field.attname, flat=True)
        queryset = queryset.order_by(field.attname).distinct()

        if term := request.GET.get('term'):
            # FIXME: How to handle very big search results?
            queryset = queryset.filter(**{f'{field.attname}__icontains': term})
            more = False

        else:
            page = int(request.GET.get('page', 1))
            start = (page - 1) * self.paginate_by
            end = page * self.paginate_by
            count = queryset.count()
            queryset = queryset[start:end]
            more = count > end

        result = dict(
            results=[dict(id=v, text=v) for v in queryset],
            pagination=dict(more=more),
        )
        return Response(result)
