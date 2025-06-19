from django import forms
from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType
from ..models import Search
from .searchkit import SearchkitModelForm
from .searchkit import searchkit_formset_factory
from .utils import MediaMixin


class SearchForm(MediaMixin, forms.ModelForm):
    """
    Represents a SearchkitSearch model. Using a SearchkitFormSet for the data
    json field.
    """
    class Meta:
        model = Search
        fields = ['name']

    @cached_property
    def searchkit_model(self):
        if self.instance.pk:
            return self.instance.contenttype.model_class()
        elif self.searchkit_model_form.is_valid():
            return self.searchkit_model_form.cleaned_data['searchkit_model'].model_class()
        elif 'searchkit_model' in self.searchkit_model_form.initial:
            value = self.searchkit_model_form.initial['searchkit_model']
            try:
                return self.searchkit_model_form.fields['searchkit_model'].clean(value).model_class()
            except forms.ValidationError:
                return None

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
