from django import forms
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.admin import widgets
from django.forms.models import ModelChoiceIterator
from django.utils.translation import gettext_lazy as _
from . import widgets as skwidgets


class BaseRangeField(forms.MultiValueField):
    field_type = None
    widget_type = None
    error_message = _("Enter 'From' and 'To' value of the range.")
    default_error_messages = {
        "invalid": error_message,
        "incomplete": error_message,
    }

    def __init__(self, **kwargs):
        widget = skwidgets.RangeWidget(widgets=[self.widget_type(), self.widget_type()])
        fields = (self.field_type(), self.field_type())
        super().__init__(
            fields=fields,
            widget=widget,
            require_all_fields=True,
            **kwargs
        )

    def compress(self, data_list):
        """We want the data list as data list."""
        return data_list


class IntegerRangeField(BaseRangeField):
    field_type = forms.IntegerField
    widget_type = forms.NumberInput


class FloatRangeField(IntegerRangeField):
    field_type = forms.FloatField


class DecimalRangeField(IntegerRangeField):
    field_type = forms.DecimalField


class DateRangeField(BaseRangeField):
    field_type = forms.DateField
    widget_type = widgets.AdminDateWidget


class TimeRangeField(BaseRangeField):
    field_type = forms.TimeField
    widget_type = widgets.AdminTimeWidget


class DateTimeRangeField(BaseRangeField):
    field_type = forms.SplitDateTimeField
    widget_type = widgets.AdminSplitDateTime


class FieldChoiceIterator(ModelChoiceIterator):
    """
    The ModelChoiceIterator do what we need. We just build our choices based
    on a field value and not an object.
    """
    def choice(self, value):
        return (value, value)


class Select2Mixin:
    """
    Get choices based on the distinct values of a model field.
    We took some code and inspiration from django's ModelChoiceField.
    """
    iterator = FieldChoiceIterator

    def __init__(self, model_field, *args, **kwargs):
        self.model_field = model_field
        self.model = model_field.model
        self.queryset = self._get_queryset()
        # ModelChoiceIterator expects an empty_label attribute.
        self.empty_label = None
        super().__init__(*args, **kwargs)

    def _get_queryset(self):
        lookup = self.model_field.attname
        queryset = self.model.objects.all()
        queryset = queryset.values_list(lookup, flat=True)
        # We order by our field to neutralize former ordering which might
        # interfere with the sql distinct statement.
        queryset = queryset.order_by(lookup)
        queryset = queryset.distinct()
        return queryset

    def _set_queryset(self, queryset):
        self._queryset = None if queryset is None else queryset.all()
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)

    def _get_choices(self):
        # FIXME: This comes from django core. But I wonder if the choices are
        # accessed multiple times, won't we evaluate the queryset each time a
        # new? It does make sense to me yet.


        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh ModelChoiceIterator that has not been
        # consumed. Note that we're instantiating a new ModelChoiceIterator *each*
        # time _get_choices() is called (and, thus, each time self.choices is
        # accessed) so that we can ensure the QuerySet has not been consumed. This
        # construct might look complicated but it allows for lazy evaluation of
        # the queryset.
        return self.iterator(self)

    choices = property(_get_choices, forms.ChoiceField.choices.fset)

    def _get_url(self):
        base_url = reverse('searchkit-autocomplete')
        url_params = {
            'sk_autocomplete_app_label': self.model._meta.app_label,
            'sk_autocomplete_model_name': self.model._meta.model_name,
            'sk_autocomplete_field_name': self.model_field.attname,
        }
        return f'{base_url}?{urlencode(url_params)}'

    def widget_attrs(self, widget):
        """
        Set select2's AJAX attributes.

        Attributes can be set using the html5 data attribute.
        Nested attributes require a double dash as per
        https://select2.org/configuration/data-attributes#nested-subkey-options
        """
        attrs = super().widget_attrs(widget)
        attrs.update({
            "class": 'admin-autocomplete',
            "data-placeholder": "search...",
            "data-theme": "admin-autocomplete",
            "data-ajax--dataType": 'json',
            "data-allow-clear": 'false',
            "data-ajax--type": "GET",
            "data-ajax--delay": 250,
            "data-ajax--url": self._get_url(),
            "data-ajax--cache": "true",
        })
        return attrs


class Select2Field(Select2Mixin, forms.ChoiceField):
    widget = skwidgets.Select2


class MultiSelect2Field(Select2Mixin, forms.MultipleChoiceField):
    widget = skwidgets.MultiSelect2
