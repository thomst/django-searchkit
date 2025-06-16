from django import forms
from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType
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
        elif 'app_label' in self.initial and 'model' in self.initial:
            kwargs['model'] = ContentType.objects.get_by_natural_key(
                app_label=self.initial['app_label'],
                model=self.initial['model']).model_class()
        elif 'contenttype_id' in self.initial:
            kwargs['model'] = ContentType.objects.get(pk=self.initial['contenttype_id']).model_class()
        return SearchkitFormSet(**kwargs)

    def is_valid(self):
        return self.formset.is_valid() and super().is_valid()

    def clean(self):
        if self.formset.contenttype_form.is_valid():
            self.instance.contenttype = self.formset.contenttype_form.cleaned_data['contenttype']
        if self.formset.is_valid():
            self.instance.data = self.formset.cleaned_data
        return super().clean()
