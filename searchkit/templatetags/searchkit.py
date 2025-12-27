from django.template import Library
from django.contrib.admin.helpers import Fieldset


# Normalize fieldsets for Django <5.1. Django 5.1 introduced the
# `is_collapsible` method on Fieldset and uses a slightly different template for
# rendering collapsible fieldsets using the details and summary HTML elements.
# Overwriting the fieldset template and adding the `is_collapsible` property we
# ensure to be backward compatible.
Fieldset.is_collapsible = property(
    lambda self: 'collapse' in self.classes and not self.form.errors
    )


register = Library()

def as_fieldset(form, name, prefix, index=None, classes=None):
    """
    Create and render a fieldset for form.
    """
    classes = classes or []
    fieldset = Fieldset(form, name=name, fields=form.fields, classes=classes)
    context = dict(
        fieldset=fieldset,
        heading_level=2,
        prefix=prefix,
        id_prefix=index,
        id_suffix=index,
    )
    return context


@register.inclusion_tag("admin/includes/fieldset.html")
def as_searchkit_model_fieldset(form):
    """
    Render a searchkit model form as fieldset.
    """
    name = "Search model"
    prefix="searchkit_model"
    return as_fieldset(form, name, prefix)


@register.inclusion_tag("admin/includes/fieldset.html")
def as_filter_logic_fieldset(form, index):
    """
    Render a filter logic form as fieldset.
    """
    name = f"Filter logic {index}"
    prefix = "searchkit"
    classes = ["searchkit", "filter-logic", "collapse"]
    return as_fieldset(form, name, prefix, index, classes)


@register.inclusion_tag("admin/includes/fieldset.html")
def as_filter_rule_fieldset(form, index):
    """
    Render a filter rule form as fieldset.
    """
    name = f"Filter rule {index}"
    prefix = "searchkit"
    classes = ["searchkit", "filter-rule", "collapse"]
    return as_fieldset(form, name, prefix, index, classes)
