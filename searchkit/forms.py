from django import forms
from searchkit.models import SearchkitSearch


class SearchkitSearchForm(forms.ModelForm):
    class Meta:
        model = SearchkitSearch
        fields = ['name', 'contenttype']
        widgets = {'contenttype': forms.HiddenInput()}
