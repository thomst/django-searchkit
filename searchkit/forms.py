from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from django.forms.formsets import TOTAL_FORM_COUNT
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
    # We need a dummy field for data. Otherwise the formset data won't be
    # handled by the ModelAdmin.
    # TODO: This is doggy. But I don't know how to handle this better.
    data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = SearchkitSearch
        fields = ['name', 'contenttype']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the contenttype field if an initial value is passed.
        if 'contenttype' in self.initial:
            self.fields['contenttype'].widget = forms.HiddenInput()

    @property
    def media(self):
        # TODO: Check if child classes inherit those media files.
        return self.formset.media

    @cached_property
    def formset_model(self):
        """
        Try hard to get a model class related to the contenttype field.
        """
        if 'contenttype' in self.initial:
            if isinstance(self.initial['contenttype'], ContentType):
                return self.initial['contenttype'].model_class()
            elif isinstance(self.initial['contenttype'], int):
                try:
                    return ContentType.objects.get(id=self.initial['contenttype']).model_class()
                except ContentType.DoesNotExist:
                    return None
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

    def get_formset_data(self):
        """
        Do we have any formset related data? Otherwise the formset was not
        rendered yet. We do not want a bound formset with no management_form
        data.
        """
        if self.data and any(key.endswith(TOTAL_FORM_COUNT) for key in self.data.keys()):
            return self.data
        else:
            return None

    @cached_property
    def formset(self):
        """
        A searchkit formset for the model.
        """
        if self.formset_model:
            data = self.get_formset_data()
            return SearchkitFormSet(self.formset_model, data=data, prefix=self.prefix)

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
            raise forms.ValidationError("Invalid filter rules. Please correct the errors below.")
        return cleaned_data

    def __str__(self):
        """
        We simply add the rendered formset to the form.
        """
        if self.formset:
            return super().__str__() + self.formset.render()
        else:
            return super().__str__()
