from modeltree import ModelTree as BaseModelTree
from collections import OrderedDict
from django.contrib.admin.widgets import AdminDateWidget, AdminSplitDateTime
from django.db import models
from django import forms
from django.utils.translation import gettext_lazy as _
from . import fields as  searchkit_fields


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
    'range': _('is between'),
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
            'range': lambda f: searchkit_fields.IntegerRangeField(),
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
            'range': lambda f: searchkit_fields.IntegerRangeField(),
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
            'range': lambda f: searchkit_fields.IntegerRangeField(),
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
            'range': lambda f: searchkit_fields.IntegerRangeField(),
        }
    ),
    (
        lambda f: isinstance(f, models.DateTimeField),
        {
            'exact': lambda f: forms.DateTimeField(),
            'gt': lambda f: forms.DateTimeField(),
            'gte': lambda f: forms.DateTimeField(),
            'lt': lambda f: forms.DateTimeField(),
            'lte': lambda f: forms.DateTimeField(),
            'range': lambda f: searchkit_fields.DateTimeRangeField(),
        }
    ),
    (
        lambda f: isinstance(f, models.DateField),
        {
            'exact': lambda f: forms.DateField(),
            'gt': lambda f: forms.DateField(),
            'gte': lambda f: forms.DateField(),
            'lt': lambda f: forms.DateField(),
            'lte': lambda f: forms.DateField(),
            'range': lambda f: searchkit_fields.DateRangeField(),
        }
    ),
))


class CssClassMixin:
    reload_on_change_css_class = "searchkit-reload-on-change"
    reload_on_click_css_class = "searchkit-reload-on-click"


class MediaMixin:
    class Media:
        js = [
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/jquery.init.js',
            "searchkit/searchkit.js"
        ]
