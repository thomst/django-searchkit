from django.template import Library
from django.contrib.admin.helpers import Fieldset


register = Library()

@register.inclusion_tag("admin/includes/fieldset.html")
def as_fieldset(form, name, prefix='searchkit', id_prefix=0, id_suffix=0):
    """
    Create and render a fieldset for form.
    """
    fieldset = Fieldset(form, name=name, fields=form.fields)
    context = dict(
        fieldset=fieldset,
        heading_level=2,
        prefix=prefix,
        id_prefix=id_prefix,
        id_suffix=id_suffix,
    )
    return context
