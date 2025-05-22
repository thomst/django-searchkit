from django.template import Library
from django.urls import reverse
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
