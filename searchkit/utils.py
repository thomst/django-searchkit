from collections import OrderedDict
from modeltree import ModelTree as BaseModelTree
from django import forms
from django.db import models
from django.contrib import admin
from django.contrib.admin import widgets
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from . import fields as  skfields


def is_searchable_model(model):
    """
    Check if the model is searchable by Searchkit.
    """
    # FIXME: This fails if someone uses a custom searchkit filter class.
    # We do not import SearchkitFilter to avoid circular imports. So we check
    # the filter by its name.
    return (
        admin.site.is_registered(model)
        and 'SearchkitFilter' in [getattr(f, '__name__', '') for f in admin.site._registry[model].list_filter]
    )


def get_value_representation(value):
    """
    Get a string representation of a value for display in the admin.
    """
    if isinstance(value, list):
        return f'[{", ".join(get_value_representation(v) for v in value)}]'
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        # FIXME: Consider rendering special types explicitly to have more control.
        # Use template rendering to get proper representation of special value
        # types like date and datetime.
        template = Template("{{ value }}")
        return template.render(Context({'value': value}))


def flatten_option_group_choices(choices):
    """
    Flatten option group choices into a simple list of choices.
    """
    flat_choices = []
    for choice in choices:
        if isinstance(choice[1], (list, tuple)):
            flat_choices.extend(choice[1])
        else:
            flat_choices.append(choice)
    return flat_choices


# TODO: Make modeltree parameters configurable.
class ModelTree(BaseModelTree):
    MAX_DEPTH = 3
    FOLLOW_ACROSS_APPS = True


class FieldPlan:
    """
    A class holding all the logic to build a dynamic searchkit form. This
    includes building the choices for the lookup and operator form fields as
    well as choosing the right form field for the value.

    There are also some meta data included to build the media property of the
    searchkit formset.
    """

    TRUE_FALSE_CHOICES = (
        (True, _('Yes')),
        (False, _('No'))
    )

    OPERATOR_DESCRIPTION = {
        'isnull': _('is null'),
        'exact': _('is exact'),
        'iexact': _('is exact'),
        'contains': _('contains'),
        'icontains': _('contains'),
        'startswith': _('starts with'),
        'istartswith': _('starts with'),
        'endswith': _('ends with'),
        'iendswith': _('ends with'),
        'regex': _('matches regular expression'),
        'iregex': _('matches regular expression'),
        'gt': _('is greater than'),
        'gte': _('is greater than or equal'),
        'lt': _('is lower than'),
        'lte': _('is lower than or equal'),
        'range': _('is within range'),
        'in': _('is one of'),
    }

    CHARACTER_FIELD_TYPES = (
        models.CharField,
        models.TextField,
        models.EmailField,
        models.URLField,
        models.UUIDField,  # TODO: Does this work with standard operators?
    )

    ARITHMETIC_FIELD_TYPES = (
        models.IntegerField,
        models.BigIntegerField,
        models.DecimalField,
        models.FloatField,
        models.DateField,
        models.TimeField,
        models.DateTimeField,
    )

    SUPPORTED_FIELD_TYPES = (
        models.BooleanField,
        *CHARACTER_FIELD_TYPES,
        *ARITHMETIC_FIELD_TYPES,
    )

    RANGE_FORM_FIELD_TYPES = (
        skfields.IntegerRangeField,
        skfields.DecimalRangeField,
        skfields.FloatRangeField,
        skfields.DateRangeField,
        skfields.TimeRangeField,
        skfields.DateTimeRangeField,
    )


    def __init__(self, model, initial=None):
        self.model = model
        self.model_tree = ModelTree(model)
        self.initial = initial or dict()
        self.field_lookup = None
        self.model_field = None

    def _get_model_field(self):
        # Split the lookup. The last piece will be the field name. Everything
        # else are relational fields.
        path = self.field_lookup.split('__')

        # If we have a path to a related model we use the model tree.
        if len(path) > 1:
            model = self.model_tree.get('__'.join(path[:-1])).model
        else:
            model = self.model

        return model._meta.get_field(path[-1])

    def get_field_lookup_choices(self):
        # Not all fields have a verbose_name attribute.
        get_field_name = lambda f: str(getattr(f, 'verbose_name', f.name))
        choices = []

        # Iterate the model tree...
        for node in self.model_tree.iterate():

            # Create a new option group for each model.
            if node.is_root:
                opt_group = (None, [])
            else:
                relations = ['one_to_one', 'many_to_one', 'one_to_many', 'many_to_many']
                relation = [r.replace('_', '-') for r in relations if getattr(node.field, r)][0]
                group_label = ' . '.join([get_field_name(n.field) for n in node.path[1:]])
                group_label += f' => {node.model._meta.app_label.title()} | {node.model._meta.verbose_name} ({relation})'
                opt_group = (group_label, [])

            # Loop the model fields to build the option group.
            for model_field in node.model._meta.get_fields():

                # Skip unsupported fields that are no relational fields.
                if (
                    not model_field.is_relation
                    and not isinstance(model_field, self.SUPPORTED_FIELD_TYPES)
                ):
                    continue

                # Skip relational fields that could not be null.
                elif (
                    model_field.is_relation
                    and (model_field.one_to_one or model_field.many_to_one)
                    and not model_field.null
                ):
                    continue

                # Prevent reversion of relational fields.
                elif model_field.is_relation and model_field.remote_field == node.field:
                    continue

                if node.is_root:
                    lookup = model_field.name
                    label = get_field_name(model_field)
                else:
                    lookup = f'{node.field_path}__{model_field.name}'
                    label = ' . '.join([get_field_name(n.field) for n in node.path[1:]] + [get_field_name(model_field)])

                opt_group[1].append((lookup, label))

            # Append the option group to the choices.
            choices.append(opt_group)

        return choices

    def get_operator_choices(self, field_lookup):
        self.field_lookup = field_lookup
        self.model_field = self._get_model_field()
        operators = OrderedDict()
        operators[None] = []

        if isinstance(self.model_field, models.BooleanField):
            operators[None] = ['exact']

        elif isinstance(self.model_field, models.TextField):
            operators['case insensitive'] = ['icontains', 'istartswith', 'iendswith', 'iregex']
            operators['case sensitive'] = ['contains', 'startswith', 'endswith', 'regex']

        elif isinstance(self.model_field, self.CHARACTER_FIELD_TYPES):
            operators['case insensitive'] = ['iexact', 'icontains', 'istartswith', 'iendswith', 'iregex']
            operators['case sensitive'] = ['exact', 'contains', 'startswith', 'endswith', 'regex', 'in']

        elif isinstance(self.model_field, self.ARITHMETIC_FIELD_TYPES):
            operators[None] = ['exact', 'gt', 'gte', 'lt', 'lte', 'range']

        elif self.model_field.is_relation:
            operators[None] = ['isnull']

        # Add an isnull lookup for model fields allowing null values.
        # Exclude relational fields since they already have an isnull operator.
        # Exclude boolean fields since they are handled with a null boolean form
        # field.
        if (
            self.model_field.null
            and not self.model_field.is_relation
            and not isinstance(self.model_field, models.BooleanField)
        ):
            operators[None] = [*operators[None], 'isnull']

        # Build the final choices list.
        return [(g, [(l, self.OPERATOR_DESCRIPTION[l]) for l in o]) for g, o in operators.items()]

    def get_form_field(self, operator):
        model_field_class = type(self.model_field)

        # Use a simple boolean form field for the isnull operator.
        if operator == 'isnull':
            form_field = forms.BooleanField(
                required=False,
                widget=forms.Select(choices=self.TRUE_FALSE_CHOICES),
                )

        # Create form field for character based field types.
        elif isinstance(self.model_field, self.CHARACTER_FIELD_TYPES):

            # With these operators we use a standard search term field.
            if operator in ['iexact', 'contains', 'icontains', 'startswith',
                            'istartswith', 'endswith', 'iendswith', 'regex', 'iregex']:
                form_field = forms.CharField(widget=widgets.AdminTextInputWidget)

            # Use a choice field for exact and in operators.
            # FIXME: We might should use a simple ChoiceField if the model's
            # field have choices defined.
            elif operator in ['exact', 'in']:
                if operator == 'exact':
                    form_field = skfields.Select2Field(self.model_field)
                elif operator == 'in':
                    form_field = skfields.MultiSelect2Field(self.model_field)

        # Handle arithmentic based field types.
        elif isinstance(self.model_field, self.ARITHMETIC_FIELD_TYPES):
            # Use range fields for the range operator.
            if operator == 'range':

                # We choose the appropriate range field based on the class names.
                test = lambda k: k.__name__.replace('Range', '') == model_field_class.__name__
                try:
                    klass = [k for k in self.RANGE_FORM_FIELD_TYPES if test(k)][0]

                # Some model fields like AutoField have no equivalent range
                # field. Those are fine with the IntegerRangeField.
                except IndexError:
                    klass = skfields.IntegerRangeField

                form_field = klass()

            # For exact operator only use a choice field if the model field has
            # choices.
            elif operator == 'exact' and self.model_field.choices:
                form_field = forms.ChoiceField(choices=self.model_field.choices)

            # TODO: Check the core code on how they use the defaults.

            # For all other operators we use the field specific default.
            else:
                # These django-admin default definition specifies widgets and
                # form classes which are utilized by the django admin site. This
                # way we get access to the famous calender widget of
                # django-admin for date and datetime fields.
                defaults = FORMFIELD_FOR_DBFIELD_DEFAULTS.get(model_field_class, dict()).copy()

                # Do we have a form class within the defaults? (True for the
                # split-date-time-field.)
                klass = defaults.pop('form_class', None)

                # Otherwise get the type of the formfield returned by the model
                # field.
                _form_field = self.model_field.formfield()
                klass = klass or type(_form_field) if _form_field else None

                # Model fields as AutoField and BigAutoField return None for
                # formfield(). So we use an IntegerField as backup.
                klass = klass or forms.IntegerField

                # Initialize the formfield.
                form_field = klass(**defaults)

        # Handle BooleanField
        elif isinstance(self.model_field, models.BooleanField):
            # The formfield method is aware of the null attribute and returns a
            # null-boolean form field.
            if self.model_field.null:
                form_field = self.model_field.formfield()

            # Otherwise we use a Select widget with True and False.
            else:
                form_field = forms.BooleanField(
                    required=False,
                    widget=forms.Select(choices=self.TRUE_FALSE_CHOICES),
                    )

        # Raise an error if we cannot build a form field.
        else:
            raise ValueError("Cannot build a form field for the given model field and operator.")

        return form_field
