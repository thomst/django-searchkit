from django.template import Library
from django.contrib.admin.helpers import Fieldset


# Normalize fieldsets for Django <5.1. Django 5.1 introduced the
# `is_collapsible` method on Fieldset and uses a slightly different template for
# rendering collapsible fieldsets using the details and summary HTML elements.
# Overwriting the fieldset template and adding the `is_collapsible` property we
# ensure to be backward compatible.
Fieldset.is_collapsible = property(lambda self: 'collapse' in self.classes)


register = Library()

@register.inclusion_tag("admin/includes/fieldset.html")
def as_fieldset(form, name=None, prefix='searchkit', index=0, classes=None):
    """
    Create and render a fieldset for form.
    """
    classes = classes.split(' ') if classes else []
    fieldset = Fieldset(form, name=name, fields=form.fields, classes=classes)
    context = dict(
        fieldset=fieldset,
        heading_level=2,
        prefix=prefix,
        id_prefix=index,
        id_suffix=index,
    )
    return context
