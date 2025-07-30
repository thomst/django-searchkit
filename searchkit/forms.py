from django import forms
from django.db import models
from django.apps import apps
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin import widgets
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from .models import Search
from .utils import ModelTree
from .utils import is_searchable_model
from . import fields as  skfields


RELOAD_CSS_CLASS = "searchkit-reload"

TRUE_FALSE_CHOICES = (
    (True, _('Yes')),
    (False, _('No'))
)


# TODO: Check unique_together contraint for search name and content type.
class SearchForm(forms.ModelForm):
    """
    Represents a SearchkitSearch model. Using a SearchkitFormSet for the data
    json field.
    """
    class Meta:
        model = Search
        fields = ['name']

    @property
    def media(self):
        return super().media + self.formset.media

    @cached_property
    def searchkit_model(self):
        # Try hard to get a model to work with.
        # First we look for a valid searchkit-model form.
        if self.searchkit_model_form.is_valid():
            return self.searchkit_model_form.cleaned_data['searchkit_model'].model_class()

        # Second we use the search instance if it exists.
        elif self.instance.pk:
            return self.instance.contenttype.model_class()

        # At least check initials for a searchkit model value and use our model
        # form to validate it.
        elif 'searchkit_model' in self.searchkit_model_form.initial:
            value = self.searchkit_model_form.initial['searchkit_model']
            try:
                cleaned_value = self.searchkit_model_form.fields['searchkit_model'].clean(value)
            except forms.ValidationError:
                return None
            else:
                return cleaned_value.model_class()

    @cached_property
    def searchkit_model_form(self):
        kwargs = dict()
        if self.data:
            kwargs['data'] = self.data
        elif self.instance.pk:
            kwargs['initial'] = dict(searchkit_model=self.instance.contenttype)
        elif self.initial:
            kwargs['initial'] = dict(searchkit_model=self.initial.get('searchkit_model'))
        return SearchkitModelForm(**kwargs)

    @cached_property
    def formset(self):
        """
        A searchkit formset for the model.
        """
        kwargs = dict()
        if self.searchkit_model and self.data:
            kwargs = dict(data=self.data)
        elif self.searchkit_model and self.instance.pk:
            kwargs = dict(initial=self.instance.data)

        extra = 0 if self.instance.pk else 1
        formset = searchkit_formset_factory(model=self.searchkit_model, extra=extra)
        return formset(**kwargs)

    def is_valid(self):
        return self.formset.is_valid() and self.searchkit_model_form.is_valid and super().is_valid()

    def clean(self):
        if self.searchkit_model_form.is_valid():
            self.instance.contenttype = self.searchkit_model_form.cleaned_data['searchkit_model']
        if self.formset.is_valid():
            self.instance.data = self.formset.cleaned_data
        return super().clean()


class SearchkitModelForm(forms.Form):
    """
    Form to select a content type.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        models = [m for m in apps.get_models() if is_searchable_model(m)]
        ids = [ContentType.objects.get_for_model(m).id for m in models]
        queryset = self.fields['searchkit_model'].queryset.filter(pk__in=ids)
        self.fields['searchkit_model'].queryset = queryset

    searchkit_model = forms.ModelChoiceField(
        queryset=ContentType.objects.all().order_by('app_label', 'model'),
        label=_('Model'),
        empty_label=_('Select a Model'),
        widget=forms.Select(attrs={
            "class": RELOAD_CSS_CLASS,
            "data-reload-handler": "change",
            "data-total-forms": 1,
        }),
    )


class FieldPlan:
    """
    A class holding all the logic to build a dynamic searchkit form. This
    includes building the choices for the lookup and operator form fields as
    well as choosing the right form field for the value.

    There are also some meta data included to build the media property of the
    searchkit formset.
    """

    OPERATOR_DESCRIPTION = {
        'isnull': _('is null'),
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
        get_field_name = lambda f: getattr(f, 'verbose_name', f.name)
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
                    and (model_field.one_to_one or model_field.one_to_many)
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

        if isinstance(self.model_field, models.BooleanField):
            operators = ['exact']

        elif isinstance(self.model_field, models.TextField):
            operators = ['contains', 'startswith', 'endswith', 'regex']

        elif isinstance(self.model_field, self.CHARACTER_FIELD_TYPES):
            operators = ['exact', 'contains', 'startswith', 'endswith', 'regex', 'in']

        elif isinstance(self.model_field, self.ARITHMETIC_FIELD_TYPES):
            operators = ['exact', 'gt', 'gte', 'lt', 'lte', 'range']

        elif self.model_field.is_relation:
            operators = ['isnull']

        # Add an isnull lookup for model fields allowing null values.
        # Exclude relational fields since they already have an isnull operator.
        # Exclude boolean fields since they are handled with a null boolean form
        # field.
        if (
            self.model_field.null
            and not self.model_field.is_relation
            and not isinstance(self.model_field, models.BooleanField)
        ):
            operators = [*operators, 'isnull']

        # Use an option group to be consistent with the field lookup choices.
        return [(None, [(o, self.OPERATOR_DESCRIPTION[o]) for o in operators])]

    def get_form_field(self, operator):
        model_field_class = type(self.model_field)

        # Use a simple boolean form field for the isnull operator.
        if operator == 'isnull':
            form_field = forms.BooleanField(
                required=False,
                widget=forms.Select(choices=TRUE_FALSE_CHOICES),
                )

        # Create form field for character based field types.
        elif isinstance(self.model_field, self.CHARACTER_FIELD_TYPES):

            # With these operators we use a standard search term field.
            if operator in ['contains', 'startswith', 'endswith', 'regex']:
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
                    widget=forms.Select(choices=TRUE_FALSE_CHOICES),
                    )

        return form_field


class LogicalStructureForm(forms.Form):
    """
    This form represents elements of the logic structure of a search.
    """
    logical_operator = forms.ChoiceField(
        choices=[
            ('and', _('AND (conjunction)')),
            ('or', _('OR (disjunction)')),
            ('xor', _('XOR (exclusive disjunction)')),
        ],
        required=False,
        label=_('Combine by'),
        help_text=_('Logical operator to combine this filter rule with the last one.'),
    )
    negation = forms.BooleanField(
        required=False,
        label=_('Use negation'),
        widget=forms.Select(choices=TRUE_FALSE_CHOICES),
        help_text=_('Negate this filter rule using a NOT statement in sql.'),
    )


class BaseSearchkitForm(forms.Form):
    """
    Searchkit form representing a queryset filter rule.

    Based on the model three fields are dynamically created:
    * The "Model field" field with model field lookup paths as choices.
    * The operator field with lookup types as choices.
    * A value field which is created based on the model field and the operator.

    Additionally there is an exclude boolean field which marks filter rules that
    should be used to exclude objects from the search result.
    """
    model = None  # Set by the formset factory.
    html_attrs = {
        "class": RELOAD_CSS_CLASS,
        "data-reload-handler": "change",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_plan = FieldPlan(self.model, self.initial)
        self._add_field_lookup_field()
        self._add_operator_field()
        self._add_value_field()

    def is_valid(self):
        # Valid if the form itself and the logic form is valid.
        return super().is_valid() and self.logic_form.is_valid()

    def clean(self):
        # Add the logic form data to the cleaned data.
        cleaned_data = super().clean()
        if self.logic_form.is_valid():
            cleaned_data.update(self.logic_form.cleaned_data)
        return cleaned_data

    @cached_property
    def logic_form(self):
        """
        Returns a form for the logical structure of a search.
        """
        kwargs = dict(prefix=self.prefix)
        if self.data:
            kwargs['data'] = self.data
        elif self.initial:
            kwargs['initial'] = self.initial

        # Return a new instance of the logical structure form.
        return LogicalStructureForm(**kwargs)

    @cached_property
    def unprefixed_data(self):
        data = dict()
        for key, value in self.data.items():
            if key.startswith(self.prefix):
                data[key[len(self.prefix) + 1:]] = value
        return data

    def _get_field_value(self, field_name):
        # Get all choices values.
        choices = self.fields[field_name].choices
        flattened_choices = [c[0] for sublist in choices for c in sublist[1]]

        # Try the initial value first since it is already cleaned.
        if self.initial and field_name in self.initial:
            return self.initial[field_name]
        # Otherwise look up the data dict.
        elif (
            field_name in self.unprefixed_data
            and self.unprefixed_data[field_name] in flattened_choices
        ):
            return self.unprefixed_data[field_name]
        else:
            # At a default return the first option which will be the selected
            # one.
            return  flattened_choices[0]

    def _add_field_lookup_field(self):
        choices = self.field_plan.get_field_lookup_choices()
        field = forms.ChoiceField(label=_('Model field'), choices=choices)
        field.widget.attrs.update(self.html_attrs)
        self.fields['field'] = field

    def _add_operator_field(self):
        field_lookup = self._get_field_value('field')
        choices = self.field_plan.get_operator_choices(field_lookup)
        field = forms.ChoiceField(label=_('Operator'), choices=choices)
        field.widget.attrs.update(self.html_attrs)
        self.fields['operator'] = field

    def _add_value_field(self):
        operator = self._get_field_value('operator')
        form_field = self.field_plan.get_form_field(operator)
        self.fields['value'] = form_field


class BaseSearchkitFormSet(forms.BaseFormSet):
    """
    Formset holding all searchkit forms.
    """
    template_name = "searchkit/searchkit.html"
    template_name_div = "searchkit/searchkit.html"
    model = None  # Set by the formset factory.

    def add_prefix(self, index):
        return "%s-%s-%s-%s" % (self.prefix, self.model._meta.app_label, self.model._meta.model_name, index)

    @classmethod
    def get_default_prefix(self):
        return "searchkit"

    @cached_property
    def forms(self):
        if self.model:
            return super().forms
        else:
            return []

    @property
    def media(self):
        # We build a media collection including everything that might be needed
        # by reloaded versions of the formset. So we do not have to dynamically
        # update media assets on the client site.

        # Basic searchkit media.
        media = forms.Media(js=[
            "searchkit/js/searchkit.js",
            "searchkit/js/widgets/fieldset.js",
            "searchkit/js/widgets/datetime.js",
            "searchkit/js/widgets/select2.js",
        ])

        # Get media assets for calender and select2 widgets.
        media += widgets.AdminSplitDateTime().media
        media += widgets.AutocompleteSelect(None, None).media

        return media

    def get_context(self):
        context = super().get_context()
        context.update(
            sk_reload_css_class=RELOAD_CSS_CLASS,
            sk_reload_url=reverse('searchkit-reload'),
            sk_total_form_count=self.total_form_count,
        )
        return context


def searchkit_formset_factory(model, **kwargs):
    form = type('SearchkitForm', (BaseSearchkitForm,), dict(model=model))
    formset = type('SearchkitFormSet', (BaseSearchkitFormSet,), dict(model=model))
    return forms.formset_factory(
        form=form,
        formset=formset,
        **kwargs
    )
