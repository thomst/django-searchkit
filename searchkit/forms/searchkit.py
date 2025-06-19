from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from .utils import CssClassMixin, FIELD_PLAN, OPERATOR_DESCRIPTION
from .utils import SUPPORTED_FIELDS
from .utils import ModelTree
from .utils import MediaMixin
from .utils import get_searchable_models


class SearchkitModelForm(forms.Form):
    """
    Form to select a content type.
    """
    searchkit_model = forms.ModelChoiceField(
        queryset=get_searchable_models(),
        label=_('Model'),
        empty_label=_('Select a Model'),
        widget=forms.Select(attrs={
            "class": CssClassMixin.reload_on_change_css_class,
            "data-total-forms": 1,
        }),
    )


class BaseSearchkitForm(MediaMixin, CssClassMixin, forms.Form):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_tree = ModelTree(self.model)
        self.model_field = None
        self.field_plan = None
        self.operator = None
        self._add_field_name_field()
        lookup = self._preload_clean_data('field')
        self.model_field = self._get_model_field(lookup)
        self.field_plan = next(iter([p for t, p in FIELD_PLAN.items() if t(self.model_field)]))
        self._add_operator_field()
        self.operator = self._preload_clean_data('operator')
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

    def _get_model_field(self, lookup):
        path = lookup.split('__')
        field_name = path[-1]
        if path[:-1]:
            model = self.model_tree.get('__'.join(path[:-1])).model
        else:
            model = self.model
        return model._meta.get_field(field_name)

    def _get_model_field_choices(self):
        choices = list()
        label_path = list()
        for node in self.model_tree.iterate():
            label_path.append
            for model_field in node.model._meta.fields:
                if not any(isinstance(model_field, f) for f in SUPPORTED_FIELDS):
                    continue
                if node.is_root:
                    lookup = model_field.name
                    label = f'`{model_field.verbose_name}`'
                else:
                    lookup = f'{node.field_path}__{model_field.name}'
                    get_field_name = lambda f: getattr(f, 'verbose_name', f.name)
                    label_path = [f'`{get_field_name(n.field)}` => <{n.model._meta.verbose_name}>' for n in node.path[1:]]
                    label = ".".join(label_path + [f'`{model_field.verbose_name}`'])
                choices.append((lookup, label))
        return choices

    def _add_field_name_field(self):
        initial = self.initial.get('field')
        choices = self._get_model_field_choices()
        field = forms.ChoiceField(label=_('Model field'), choices=choices, initial=initial)
        field.widget.attrs.update({"class": self.reload_on_change_css_class})
        self.fields['field'] = field

    def _add_operator_field(self):
        initial = self.initial.get('operator')
        choices = [(o, OPERATOR_DESCRIPTION[o]) for o in self.field_plan.keys()]
        field = forms.ChoiceField(label=_('Operator'), choices=choices, initial=initial)
        field.widget.attrs.update({"class": self.reload_on_change_css_class})
        self.fields['operator'] = field

    def _add_value_field(self):
        initial = self.initial.get('value')
        field_class = self.field_plan[self.operator][0]
        if getattr(field_class, 'choices', None) and getattr(self.model_field, 'choices', None):
            field = field_class(choices=self.model_field.choices, initial=initial)
        else:
            field = field_class()
        self.fields['value'] = field


class BaseSearchkitFormSet(CssClassMixin, forms.BaseFormSet):
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


def searchkit_formset_factory(model, **kwargs):
    form = type('SearchkitForm', (BaseSearchkitForm,), dict(model=model))
    formset = type('SearchkitFormSet', (BaseSearchkitFormSet,), dict(model=model))
    return forms.formset_factory(
        form=form,
        formset=formset,
        **kwargs
    )
