from collections import OrderedDict
from modeltree import ModelTree as BaseModelTree
from django.contrib import admin
from django.contrib.admin import widgets
from django.utils.translation import gettext_lazy as _
from django.db import models
from django import forms
from . import fields as  skfields


def is_searchable_model(model):
    """
    Check if the model is searchable by Searchkit.
    """
    # We do not import SearchkitFilter to avoid circular imports. So we check
    # the filter by its name.
    return (
        admin.site.is_registered(model)
        and 'SearchkitFilter' in [getattr(f, '__name__', '') for f in admin.site._registry[model].list_filter]
    )


# TODO: Make modeltree parameters configurable.
class ModelTree(BaseModelTree):
    MAX_DEPTH = 3
    FOLLOW_ACROSS_APPS = True
    RELATION_TYPES = [
        'one_to_one',
        'many_to_one',
    ]


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
    'range': _('is within range'),
    'in': _('is one of'),
}


SUPPORTED_FIELDS = [
    models.BooleanField,
    models.CharField,
    models.IntegerField,
    models.FloatField,
    models.DecimalField,
    models.DateField,
    models.DateTimeField,
]


FIELD_PLAN = OrderedDict((
    (
        lambda f: isinstance(f, models.BooleanField),
        {
            'exact': lambda f: forms.NullBooleanField() if f.null else forms.BooleanField(),
        }
    ),
    (
        lambda f: isinstance(f, models.CharField) and f.choices,
        {
            'exact': lambda f: forms.ChoiceField(choices=f.choices),
            'contains': lambda f: forms.CharField(),
            'startswith': lambda f: forms.CharField(),
            'endswith': lambda f: forms.CharField(),
            'regex': lambda f: forms.CharField(),
            'in': lambda f: forms.MultipleChoiceField(choices=f.choices),
        }
    ),
    (
        lambda f: isinstance(f, models.CharField),
        {
            'exact': lambda f: forms.CharField(),
            'contains': lambda f: forms.CharField(),
            'startswith': lambda f: forms.CharField(),
            'endswith': lambda f: forms.CharField(),
            'regex': lambda f: forms.CharField(),
        }
    ),
    (
        lambda f: isinstance(f, models.IntegerField) and f.choices,
        {
            'exact': lambda f: forms.ChoiceField(choices=f.choices),
            'gt': lambda f: forms.IntegerField(),
            'gte': lambda f: forms.IntegerField(),
            'lt': lambda f: forms.IntegerField(),
            'lte': lambda f: forms.IntegerField(),
            'range': lambda f: skfields.IntegerRangeField(),
            'in': lambda f: forms.MultipleChoiceField(choices=f.choices),
        }
    ),
    (
        lambda f: isinstance(f, models.IntegerField),
        {
            'exact': lambda f: forms.IntegerField(),
            'gt': lambda f: forms.IntegerField(),
            'gte': lambda f: forms.IntegerField(),
            'lt': lambda f: forms.IntegerField(),
            'lte': lambda f: forms.IntegerField(),
            'range': lambda f: skfields.IntegerRangeField(),
        }
    ),
    (
        lambda f: isinstance(f, models.FloatField),
        {
            'exact': lambda f: forms.FloatField(),
            'gt': lambda f: forms.FloatField(),
            'gte': lambda f: forms.FloatField(),
            'lt': lambda f: forms.FloatField(),
            'lte': lambda f: forms.FloatField(),
            'range': lambda f: skfields.FloatRangeField(),
        }
    ),
    (
        lambda f: isinstance(f, models.DecimalField),
        {
            'exact': lambda f: forms.DecimalField(),
            'gt': lambda f: forms.DecimalField(),
            'gte': lambda f: forms.DecimalField(),
            'lt': lambda f: forms.DecimalField(),
            'lte': lambda f: forms.DecimalField(),
            'range': lambda f: skfields.DecimalRangeField(),
        }
    ),
    (
        lambda f: isinstance(f, models.DateTimeField),
        {
            'exact': lambda f: forms.SplitDateTimeField(widget=widgets.AdminSplitDateTime()),
            'gt': lambda f: forms.SplitDateTimeField(widget=widgets.AdminSplitDateTime()),
            'gte': lambda f: forms.SplitDateTimeField(widget=widgets.AdminSplitDateTime()),
            'lt': lambda f: forms.SplitDateTimeField(widget=widgets.AdminSplitDateTime()),
            'lte': lambda f: forms.SplitDateTimeField(widget=widgets.AdminSplitDateTime()),
            'range': lambda f: skfields.DateTimeRangeField(),
        }
    ),
    (
        lambda f: isinstance(f, models.DateField),
        {
            'exact': lambda f: forms.DateField(widget=widgets.AdminDateWidget()),
            'gt': lambda f: forms.DateField(widget=widgets.AdminDateWidget()),
            'gte': lambda f: forms.DateField(widget=widgets.AdminDateWidget()),
            'lt': lambda f: forms.DateField(widget=widgets.AdminDateWidget()),
            'lte': lambda f: forms.DateField(widget=widgets.AdminDateWidget()),
            'range': lambda f: skfields.DateRangeField(),
        }
    ),
))
