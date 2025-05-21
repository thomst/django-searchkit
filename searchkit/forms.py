from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from .models import SearchkitSearch
from .searchkit import SearchkitFormSet


# TODO: Does this work as model form?
# TODO: Dynamically use a hidden contenttype field or a choices field. Then
# reloading form on change of the choices field.
class SearchkitSearchForm(forms.ModelForm):
    """
    Represents a SearchkitSearch model. Using a SearchkitFormSet for the data
    json field.
    """
    class Meta:
        model = SearchkitSearch
        fields = ['name', 'contenttype']

    # name = forms.CharField(label='Search name', max_length=255, required=True)
    # contenttype = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        hide_contenttype_field = kwargs.pop('hide_contenttype_field', False)
        super().__init__(*args, **kwargs)
        # We need the complete data passed to instantiate the formset.
        self.formset_data = kwargs.get('data')
        # Optionally hide the contenttype field if an initial value is passed.
        if 'contenttype' in self.initial and hide_contenttype_field:
            self.fields['contenttype'].widget = forms.HiddenInput()

    @property
    def media(self):
        # TODO: Check if child classes inherit those media files.
        return self.formset.media

    @cached_property
    def formset_model(self):
        """
        Try hard to get a model class for the formset.
        """
        if 'contenttype' in self.initial:
            return self.initial['contenttype'].model_class()
        elif hasattr(self, 'cleaned_data') and 'contenttype' in self.cleaned_data:
            return self.cleaned_data['contenttype'].model_class()
        elif 'contenttype' in self.data:
            value = self.data.get(self.add_prefix('contenttype'))
            try:
                contenttype_id = self.fields['contenttype'].clean(value)
            except forms.ValidationError:
                return None
            try:
                return ContentType.objects.get(id=contenttype_id).model_class()
            except ContentType.DoesNotExist:
                return None
        else:
            contenttype_id = self.fields['contenttype'].choices[0][0]
            try:
                return ContentType.objects.get(id=contenttype_id).model_class()
            except (ValueError, ContentType.DoesNotExist):
                return None

    @cached_property
    def formset(self):
        """
        A searchkit formset for the model.
        """
        if self.formset_model:
            return SearchkitFormSet(self.formset_model, data=self.formset_data, prefix=self.prefix)

    def clean(self):
        """
        Additionally validate the formset.
        """
        cleaned_data = super().clean()
        if not self.formset:
            raise forms.ValidationError("No formset available. Please check the contenttype field.")
        if self.formset.is_valid():
            cleaned_data['data'] = self.formset.data
        else:
            raise forms.ValidationError("Invalid filter rules. Please check the errors below.")
        return cleaned_data

    def __str__(self):
        """
        We simply add the rendered formset to the form.
        """
        if self.formset:
            return super().__str__() + self.formset.render()
        else:
            return super().__str__()
