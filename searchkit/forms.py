from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import SearchkitSearch
from .searchkit import SearchkitFormSet


# TODO: Does this work as model form?
class SearchkitSearchForm(forms.Form):
    """
    Represents a SearchkitSearch model. Using a SearchkitFormSet for the data
    json field.
    """
    name = forms.CharField(label='Search name', max_length=255, required=True)
    contenttype = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, model, data=None, prefix=None, initial=None, *args, **kwargs):
        self.formset = SearchkitFormSet(model, data=data, prefix=prefix)
        initial = initial or {}
        initial['contenttype'] = ContentType.objects.get_for_model(model).id
        super().__init__(data, initial=initial, prefix=prefix, *args, **kwargs)

    @property
    def media(self):
        return self.formset.media

    def clean(self):
        """
        Additionally validate the formset.
        """
        cleaned_data = super().clean()
        if self.formset.is_valid():
            cleaned_data['data'] = self.formset.data
        else:
            raise forms.ValidationError("Formset is not valid")
        return cleaned_data

    def __str__(self):
        """
        We simply add the rendered formset to the form.
        """
        html = super().__str__()
        html += self.formset.render()
        return html
