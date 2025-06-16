from django import forms
from django.utils.functional import cached_property
from ..models import Search
from .searchkit import SearchkitFormSet


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
        # TODO: Check if child classes inherit those media files.
        return self.formset.media

    @cached_property
    def formset(self):
        """
        A searchkit formset for the model.
        """
        kwargs = dict()
        kwargs['data'] = self.data or None
        kwargs['prefix'] = self.prefix
        if self.instance.pk:
            kwargs['model'] = self.instance.contenttype.model_class()
            kwargs['initial'] = self.instance.data
        return SearchkitFormSet(**kwargs)

    def is_valid(self):
        return self.formset.is_valid() and super().is_valid()

    def clean(self):
        if self.formset.contenttype_form.is_valid():
            self.instance.contenttype = self.formset.contenttype_form.cleaned_data['contenttype']
        if self.formset.is_valid():
            self.instance.data = self.formset.cleaned_data
        return super().clean()
