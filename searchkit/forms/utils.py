from django.db import models
from django import forms
from django.utils.translation import gettext_lazy as _
from collections import OrderedDict
from searchkit.forms import fields as searchkit_fields


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
        lambda f: isinstance(f, models.CharField),
        {
            'exact': (forms.CharField,),
            'contains': (forms.CharField,),
            'startswith': (forms.CharField,),
            'endswith': (forms.CharField,),
            'regex': (forms.CharField,),
        }
    ),
    (
        lambda f: isinstance(f, models.IntegerField) and f.choices,
        {
            'exact': (forms.ChoiceField,),
            'contains': (forms.IntegerField,),
            'startswith': (forms.IntegerField,),
            'endswith': (forms.IntegerField,),
            'regex': (forms.IntegerField,),
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
            'range': (searchkit_fields.IntegerRangeField,),
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
            'range': (searchkit_fields.IntegerRangeField,),
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
            'range': (searchkit_fields.IntegerRangeField,),
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
            'range': (searchkit_fields.DateTimeRangeField,),
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
            'range': (searchkit_fields.DateRangeField,),
        }
    ),
))


class CSS_CLASSES:
    reload_on_change_css_class = "searchkit-reload-on-change"
    reload_on_click_css_class = "searchkit-reload-on-click"


def get_filter_rules(formset):
    """
    Build filter rules out of the cleaned data of the formset.
    :param formset: Formset to extract filter rules from.
    :return: OrderedDict with filter rule pairs: field__operator: value
    """
    lookups = OrderedDict()
    for data in formset.cleaned_data:
        lookups[f'{data["field"]}__{data["operator"]}'] = data['value']
    return lookups
