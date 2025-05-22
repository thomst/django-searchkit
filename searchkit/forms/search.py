from django import forms
from django.utils.functional import cached_property
from ..models import SearchkitSearch
from .searchkit import SearchkitFormSet


class SearchkitSearchForm(forms.ModelForm):
    """
    Represents a SearchkitSearch model. Using a SearchkitFormSet for the data
    json field.
    """
    class Meta:
        model = SearchkitSearch
        fields = ['name', 'contenttype', 'data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the data field. Finally we use the data of the formset.
        self.fields['data'].widget = forms.HiddenInput()
        self.fields['data'].initial = "true"  # We need some valid initial data.
        self.fields['contenttype'].widget = forms.HiddenInput()

    @property
    def media(self):
        # TODO: Check if child classes inherit those media files.
        return self.formset.media

    @cached_property
    def formset(self):
        """
        A searchkit formset for the model.
        """
        data = self.data or None
        return SearchkitFormSet(data=data, prefix=self.prefix)

    def is_valid(self):
        return self.formset.is_valid() and super().is_valid()

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['contenttype'] = self.formset.contenttype_form.cleaned_data['contenttype']
        cleaned_data['data'] = self.formset.data
        return cleaned_data
