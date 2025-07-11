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
        # Do we have an instance? Then use its model.
        if self.instance.pk:
            return self.instance.contenttype.model_class()

        # Otherwise check if we have a valid searchkit model form.
        elif self.searchkit_model_form.is_valid():
            return self.searchkit_model_form.cleaned_data['searchkit_model'].model_class()

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
        kwargs = dict(data=self.data or None, initial=self.initial or None)
        if self.instance.pk:
            kwargs['initial'] = dict(searchkit_model=self.instance.contenttype)
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
        choices = list()

        # Iterate the model tree...
        for node in self.model_tree.iterate():
            # ... and the fields of each model.
            for model_field in node.model._meta.fields:

                # Skip unsupported fields.
                if not isinstance(model_field, self.SUPPORTED_FIELD_TYPES):
                    continue

                # Build lookup and label for the root model.
                if node.is_root:
                    lookup = model_field.name
                    label = f'`{model_field.verbose_name}`'

                # Build lookup and label for related models.
                else:
                    lookup = f'{node.field_path}__{model_field.name}'
                    get_field_name = lambda f: getattr(f, 'verbose_name', f.name)
                    label_path = [
                        f'`{get_field_name(n.field)}` => <{n.model._meta.verbose_name}>'
                        for n in node.path[1:]
                        ]
                    label = ".".join(label_path + [f'`{model_field.verbose_name}`'])

                # Append the choice.
                choices.append((lookup, label))

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

        return [(o, self.OPERATOR_DESCRIPTION[o]) for o in operators]

    def get_form_field(self, operator):
        model_field_class = type(self.model_field)

        # Create form field for character based field types.
        if isinstance(self.model_field, self.CHARACTER_FIELD_TYPES):

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
            # boolean or null-boolean form field.
            form_field = self.model_field.formfield()

        return form_field


class BaseSearchkitForm(forms.Form):
    """
    Searchkit form representing a model field lookup based on the field name,
    the operator and one or two values.

    The unbound form is composed of an index field (the count of the searchkit
    form) and a choice field offering the names of the model fields.

    The bound form is dynamically extended by the operator field or the operator and
    the value field depending on the provided data

    See the FIELD_PLAN variable for the logic of building the form.
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

    @cached_property
    def unprefixed_data(self):
        data = dict()
        for key, value in self.data.items():
            if key.startswith(self.prefix):
                data[key[len(self.prefix) + 1:]] = value
        return data

    def _preload_clean_data(self, field_name):
        # Try the initial value first since it is already cleaned.
        if self.initial and field_name in self.initial:
            return self.initial[field_name]
        # Otherwise look up the data dict.
        elif field_name in self.unprefixed_data:
            try:
                # Do we have a valid value?
                return self.fields[field_name].clean(self.unprefixed_data[field_name])
            except forms.ValidationError:
                return self.fields[field_name].choices[0][0]
        else:
            # At last simply return the first option which will be the selected
            # one.
            return self.fields[field_name].choices[0][0]

    def _add_field_lookup_field(self):
        choices = self.field_plan.get_field_lookup_choices()
        field = forms.ChoiceField(label=_('Model field'), choices=choices)
        field.widget.attrs.update(self.html_attrs)
        self.fields['field'] = field

    def _add_operator_field(self):
        field_lookup = self._preload_clean_data('field')
        choices = self.field_plan.get_operator_choices(field_lookup)
        field = forms.ChoiceField(label=_('Operator'), choices=choices)
        field.widget.attrs.update(self.html_attrs)
        self.fields['operator'] = field

    def _add_value_field(self):
        operator = self._preload_clean_data('operator')
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
