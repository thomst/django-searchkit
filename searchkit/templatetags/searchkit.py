from django.template import Library
from django.urls import reverse
from django.contrib.admin.helpers import Fieldset
from ..forms.utils import CSS_CLASSES


register = Library()


@register.simple_tag
def searchkit_url(formset):
    """
    Return url to reload the formset.
    """
    app_label = formset.model._meta.app_label
    model_name = formset.model._meta.model_name
    url = reverse('searchkit_form', args=[app_label, model_name])
    return url

@register.simple_tag
def on_change_class():
    """
    Return css class for on change handler.
    """
    return CSS_CLASSES.reload_on_change_css_class

@register.simple_tag
def on_click_class():
    """
    Return css class for on click handler.
    """
    return CSS_CLASSES.reload_on_click_css_class

@register.inclusion_tag("admin/includes/fieldset.html")
def as_fieldset(form, heading_level=2, prefix='', id_prefix=0, id_suffix='', **fieldset_kwargs):
    """
    Create and render a fieldset for form.
    """
    fieldset = Fieldset(form, fields=form.fields, **fieldset_kwargs)
    context = dict(
        fieldset=fieldset,
        heading_level=heading_level,
        prefix=prefix,
        id_prefix=id_prefix,
        id_suffix=id_suffix,
    )
    return context
