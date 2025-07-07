from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.renderers import StaticHTMLRenderer
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import FieldError
from .forms import SearchkitModelForm
from .forms import searchkit_formset_factory


class InvalidModelFormException(APIException):
    status_code = 400
    default_detail = _('Invalid searchkit model form.')
    default_code = 'invalid_model_form'


class InvalidAutocompleteParameter(APIException):
    status_code = 400
    default_detail = _('Invalid autocomplete url parameter.')
    default_code = 'invalid_autocomplete_parameter'


class InvalidAutocompleteFieldLookup(InvalidAutocompleteParameter):
    status_code = 400
    default_detail = _('Invalid autocomplete field lookup: searchkit_field_lookup')
    default_code = 'invalid_autocomplete_field_lookup'


class SearchkitPermission(BasePermission):
    def has_permission(self, request, view):
        # Allow access only if the user has the 'add' or 'change' permissions.
        return (
            request.user.has_perm('searchkit.add_search')
            or request.user.has_perm('searchkit.change_search')
        )


class LookupModelPermission(BasePermission):
    def has_permission(self, request, view):
        # Allow access only if the user has the 'view' permission on the
        # searchkit model.
        model = view.get_model(request)
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        return request.user.has_perm(f'{app_label}.view_{model_name}')


class GetModelMixin:
    def get_model(self, request):
        model_form = SearchkitModelForm(data=request.GET)
        if model_form.is_valid():
            return model_form.cleaned_data['searchkit_model'].model_class()
        else:
            raise InvalidModelFormException()


class SearchkitView(GetModelMixin, APIView):
    """
    Update the searchkit formset via ajax.
    """
    permission_classes = [SearchkitPermission]
    renderer_classes = [StaticHTMLRenderer]

    def get(self, request, **kwargs):
        model = self.get_model(request)
        formset = searchkit_formset_factory(model=model)(data=request.GET)
        return Response(formset.render())


class AutocompleteView(GetModelMixin, APIView):
    """
    Autocomplete view for select2 value fields.
    """
    permission_classes = [SearchkitPermission, LookupModelPermission]
    renderer_classes = [JSONRenderer]
    pagination = 25

    def get_queryset(self, model, field_lookup):
        try:
            return model.objects.values_list(field_lookup, flat=True).distinct()
        except FieldError:
            raise InvalidAutocompleteFieldLookup()

    # FIXME: How to handle very big search results?
    def get_search_result(self, queryset, field_lookup, term):
        lookup = {f'{field_lookup}__contains': term}
        values = queryset.filter(**lookup)
        results = [dict(id=v, text=v) for v in values]
        return dict(results=results)

    def get_pagination_result(self, queryset, page):
        start = (page - 1) * self.pagination
        end = page * self.pagination
        count = queryset.count()
        more = count > end
        values = queryset[start:end]
        return dict(
            results=[dict(id=v, text=v) for v in values],
            pagination=dict(more=more)
        )

    def get(self, request, **kwargs):
        model = self.get_model(request)
        term = request.GET.get('term', None)
        page = int(request.GET.get('page', 1))
        try:
            field_lookup = request.GET['searchkit_field_lookup']
            _type = request.GET['_type']
        except KeyError:
            raise InvalidAutocompleteParameter()
        else:
            queryset = self.get_queryset(model, field_lookup)

        if term:
            result = self.get_search_result(queryset, field_lookup, term)
        else:
            result = self.get_pagination_result(queryset, page)

        return Response(result)
