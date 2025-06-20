from modeltree import ModelTree as BaseModelTree
from collections import OrderedDict
from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.utils import OperationalError
from django import forms
from django.utils.translation import gettext_lazy as _
from ..filters import SearchkitFilter
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
            'exact': (forms.NullBooleanField,),
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


def is_searchable_model(model):
    """
    Check if the model is searchable by Searchkit.
    """
    return admin.site.is_registered(model) and SearchkitFilter in admin.site._registry[model].list_filter


def get_searchable_models():
    """
    Return a queryset of searchable models.
    """
    # Before mirating the database we get an OperationalError when trying to
    # access ContentType database table.
    try:
        models = [m for m in apps.get_models() if is_searchable_model(m)]
        ids = [ContentType.objects.get_for_model(m).id for m in models]
        return ContentType.objects.filter(pk__in=ids).order_by('app_label', 'model')
    except OperationalError:
        return ContentType.objects.all()
