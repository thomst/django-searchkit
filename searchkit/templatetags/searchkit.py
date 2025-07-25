from django.template import Library
from django.contrib.admin.helpers import Fieldset


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
