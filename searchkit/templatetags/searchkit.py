from django.template import Library
from django.contrib.admin.helpers import Fieldset


register = Library()

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
