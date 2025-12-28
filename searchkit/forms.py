from django import forms
from django.apps import apps
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin import widgets
from .models import Search
from .utils import FieldPlan
from .utils import is_searchable_model


RELOAD_CSS_CLASS = "searchkit-reload"


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


# TODO: Check unique_together contraint for search name and content type.
# FIXME: Validate missing name when _apply is used.
class SearchForm(forms.ModelForm):
    """
    Represents a SearchkitSearch model. Using a SearchkitFormSet for the data
    json field.
    """
    searchkit_model_form_class = SearchkitModelForm

    class Meta:
        model = Search
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows':4, 'cols':30})}

    @property
    def media(self):
        return super().media + self.formset.media

    @cached_property
    def searchkit_model(self):
        # Try hard to get a model to work with.

        # If we have a valid searchkit_model_form we use its cleaned data.
        if self.searchkit_model_form.is_valid():
            return self.searchkit_model_form.cleaned_data['searchkit_model'].model_class()

        # If this is a bound model form we use the contenttype of the search
        # instance.
        elif self.instance.pk:
            return self.instance.contenttype.model_class()

        # If we have a valid initial value for the searchkit_model we can use it.
        elif 'searchkit_model' in self.searchkit_model_form.initial:
            value = self.searchkit_model_form.initial['searchkit_model']
            try:
                cleaned_value = self.searchkit_model_form.fields['searchkit_model'].clean(value)
            except forms.ValidationError:
                return None
            else:
                return cleaned_value.model_class()

        # Finally use the first choice if there is no empty label.
        elif self.searchkit_model_form.fields['searchkit_model'].empty_label is None:
            return self.searchkit_model_form.fields['searchkit_model'].queryset.first().model_class()

    def get_searchkit_model_form_class(self):
        return self.searchkit_model_form_class

    def get_searchkit_model_form_kwargs(self):
        kwargs = dict()
        if self.data:
            kwargs['data'] = self.data
        elif self.instance.pk:
            kwargs['initial'] = dict(searchkit_model=self.instance.contenttype)
        elif self.initial:
            kwargs['initial'] = dict(searchkit_model=self.initial.get('searchkit_model'))
        return kwargs

    def get_searchkit_model_form(self):
        kwargs = self.get_searchkit_model_form_kwargs()
        return self.get_searchkit_model_form_class()(**kwargs)

    @cached_property
    def searchkit_model_form(self):
        return self.get_searchkit_model_form()

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


class LogicalStructureForm(forms.Form):
    """
    This form represents elements of the logic structure of a search.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the logical operator for the first form.
        if int(self.prefix.split('-')[-1]) == 0:
            del self.fields['logical_operator']

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
        widget=forms.Select(choices=reversed(FieldPlan.TRUE_FALSE_CHOICES)),
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
        media = forms.Media(
            js=[
            "searchkit/js/searchkit.js",
            "searchkit/js/widgets/fieldset.js",
            "searchkit/js/widgets/datetime.js",
            "searchkit/js/widgets/select2.js",
            ],
            css={
                'all': [
                    "searchkit/css/searchkit.css",
                ]
            }
        )

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
