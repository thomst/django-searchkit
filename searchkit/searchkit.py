from collections import OrderedDict
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


class RangeWidget(forms.MultiWidget):
    def decompress(self, value):
        """The value should be already a list."""
        if value:
            return value
        else:
            return [None, None]


class BaseRangeField(forms.MultiValueField):
    def compress(self, data_list):
        """We want the data list as data list."""
        return data_list


class IntegerRangeField(BaseRangeField):
    def __init__(self, **kwargs):
        error_messages = {
            "incomplete": _("Enter the first and the last number."),
        }
        fields = (
            forms.IntegerField(label=_('From')),
            forms.IntegerField(label=_('To')),
        )
        widget = RangeWidget(widgets=[forms.NumberInput, forms.NumberInput])
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )


class DateRangeField(BaseRangeField):
    def __init__(self, **kwargs):
        error_messages = {
            "incomplete": _("Enter the first and the last date."),
        }
        fields = (
            forms.DateField(label=_('From')),
            forms.DateField(label=_('To')),
        )
        widget = RangeWidget(widgets=[forms.DateInput, forms.DateInput]),
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )


class DateTimeRangeField(BaseRangeField):
    def __init__(self, **kwargs):
        error_messages = {
            "incomplete": _("Enter the first and the last datetime."),
        }
        fields = (
            forms.DateTimeField(label=_('From')),
            forms.DateTimeField(label=_('To')),
        )
        widget = RangeWidget(widgets=[forms.DateTimeInput, forms.DateTimeInput]),
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )


DEFAULT_PREFIX = 'searchkit'


OPERATOR_DESCRIPTION = {
    'exact': _('is exact'),
    'contains': _('contains'),
    'startswith': _('starts with'),
    'endswith': _('ends with'),
    'regex': _('matches regular expression'),
    'gt': _('is greater than'),
    'gte': _('is greater than or equal'),
    'lt': _('is lower than'),
    'lte': _('is lower than or equal'),
    'range': _('is between'),
    'in': _('is one of'),
}


SUPPORTED_FIELDS = [
    models.CharField,
    models.IntegerField,
    models.FloatField,
    models.DecimalField,
    models.DateField,
    models.DateTimeField,
]


FIELD_PLAN = OrderedDict((
    (
        lambda f: isinstance(f, models.CharField) and not f.choices,
        {
            'exact': (forms.CharField,),
            'contains': (forms.CharField,),
            'startswith': (forms.CharField,),
            'endswith': (forms.CharField,),
            'regex': (forms.CharField,),
        }
    ),
    (
        lambda f: isinstance(f, models.CharField) and f.choices,
        {
            'exact': (forms.ChoiceField,),
            'contains': (forms.CharField,),
            'startswith': (forms.CharField,),
            'endswith': (forms.CharField,),
            'regex': (forms.CharField,),
            'in': (forms.MultipleChoiceField,),
        }
    ),
    (
        lambda f: isinstance(f, models.IntegerField),
        {
            'exact': (forms.IntegerField,),
            'gt': (forms.IntegerField,),
            'gte': (forms.IntegerField,),
            'lt': (forms.IntegerField,),
            'lte': (forms.IntegerField,),
            'range': (IntegerRangeField,),
            'in': (forms.CharField,),
        }
    ),
    (
        lambda f: isinstance(f, models.FloatField),
        {
            'exact': (forms.FloatField,),
            'gt': (forms.FloatField,),
            'gte': (forms.FloatField,),
            'lt': (forms.FloatField,),
            'lte': (forms.FloatField,),
            'range': (IntegerRangeField,),
        }
    ),
    (
        lambda f: isinstance(f, models.DecimalField),
        {
            'exact': (forms.DecimalField,),
            'gt': (forms.DecimalField,),
            'gte': (forms.DecimalField,),
            'lt': (forms.DecimalField,),
            'lte': (forms.DecimalField,),
            'range': (IntegerRangeField,),
        }
    ),
    (
        lambda f: isinstance(f, models.DateTimeField),
        {
            'exact': (forms.DateTimeField,),
            'gt': (forms.DateTimeField,),
            'gte': (forms.DateTimeField,),
            'lt': (forms.DateTimeField,),
            'lte': (forms.DateTimeField,),
            'range': (DateTimeRangeField,),
        }
    ),
    (
        lambda f: isinstance(f, models.DateField),
        {
            'exact': (forms.DateField,),
            'gt': (forms.DateField,),
            'gte': (forms.DateField,),
            'lt': (forms.DateField,),
            'lte': (forms.DateField,),
            'range': (DateRangeField,),
        }
    ),
))


class SearchkitForm(forms.Form):
    """
    Searchkit form representing a model field lookup based on the field name,
    the operator and one or two values.

    The unbound form is composed of an index field (the count of the searchkit
    form) and a choice field offering the names of the model fields.

    The bound form is dynamically extended by the operator field or the operator and
    the value field depending on the provided data

    See the FIELD_PLAN variable for the logic of building the form.
    """
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.model_field = None
        self.operator = None
        self.field_plan = None
        self._build_form()

    @cached_property
    def unprefixed_data(self):
        data = dict()
        for key, value in self.data.items():
            if key.startswith(self.prefix):
                data[key[len(self.prefix) + 1:]] = value
        return data

    def _build_form(self):
        """
        Add additional form fields for operator and value based on the raw data.
        """
        self._add_model_field_field()
        if self._preload_model_field_data() and 'operator' in self.unprefixed_data:
            self._add_operator_field()
            if self._preload_operator_data() and any(v in self.unprefixed_data for v in ['value', 'value_0', 'value_1']):
                self._add_value_field()

    def _preload_clean_data(self, field_name):
        try:
            return self.fields[field_name].clean(self.unprefixed_data[field_name])
        except (KeyError, forms.ValidationError):
            return None

    def _preload_model_field_data(self):
        if model_field_name := self._preload_clean_data('field'):
            self.model_field = self.model._meta.get_field(model_field_name)
            self.field_plan = next(iter([p for t, p in FIELD_PLAN.items() if t(self.model_field)]))
            return True
        else:
            return False

    def _preload_operator_data(self):
        if operator := self._preload_clean_data('operator'):
            self.operator = operator
            return True
        else:
            return False

    def _add_model_field_field(self):
        choices = list()
        for model_field in self.model._meta.fields:
            if any(issubclass(type(model_field), f) for f in SUPPORTED_FIELDS):
                choices.append((model_field.name, model_field.verbose_name))

        field = forms.ChoiceField(label=_('Model field'), choices=choices)
        self.fields['field'] = field

    def _add_operator_field(self):
        choices = [(o, OPERATOR_DESCRIPTION[o]) for o in self.field_plan.keys()]
        field = forms.ChoiceField(label=_('Operator'), choices=choices)
        self.fields['operator'] = field

    def _add_value_field(self):
        field_class = self.field_plan[self.operator][0]
        if hasattr(field_class, 'choices'):
            # FIXME: Model field do not nesseccarily has choices attribute.
            field = field_class(choices=self.model_field.choices)
        else:
            field = field_class()
        self.fields['value'] = field

    @property
    def is_complete(self):
        """
        True if the form has valid values for model_field, operator and value.
        False otherwise. Works after is_valid was called.
        """
        return len(self.cleaned_data) == 3

    def extend(self):
        """
        Add additional unbound form field for operator or value based on the
        cleaned data. Works after is_valid was called.
        """
        if len(self.cleaned_data) < 2:
            self._add_operator_field()
        elif len(self.cleaned_data) < 3:
            self._add_value_field()

    def get_filter_rule(self):
        """
        Returns lookup string and value pair if the form is valid and complete.
        Works after is_valid was called.
        """
        if self.is_complete:
            model_field = self.cleaned_data['field']
            operator = self.cleaned_data['operator']
            value = self.cleaned_data['value']
            return f'{model_field}__{operator}', value


class BaseSearchkitFormset(forms.BaseFormSet):
    """
    Formset holding all searchkit forms.
    """
    def __init__(self, model, *args, **kwargs):
        form_kwargs = kwargs.pop('form_kwargs', dict())
        form_kwargs['model'] = model
        kwargs['form_kwargs'] = form_kwargs
        super().__init__(*args, **kwargs)

    @classmethod
    def get_default_prefix(cls):
        return DEFAULT_PREFIX

    @property
    def is_complete(self):
        """
        True if all forms are completed.
        False otherwise. Works after is_valid was called.
        """
        return all(f.is_complete for f in self.forms)

    def is_valid(self):
        """
        Check if all forms are valid and complete.
        """
        return super().is_valid() and self.is_complete

    def extend(self):
        """
        Add additional unbound form field for operator or value based on the
        cleaned data for each form. Works after is_valid was called.
        """
        for form in self.forms:
            form.extend()

    def get_filter_rules(self):
        """
        Returns filter rules of all forms as list. Works after is_valid was
        called.
        """
        return OrderedDict([f.get_filter_rule() for f in self.forms])


SearchkitFormSet = forms.formset_factory(
        form=SearchkitForm,
        formset=BaseSearchkitFormset,
    )
