from modeltree import ModelTree as BaseModelTree
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context


def is_searchable_model(model):
    """
    Check if the model is searchable by Searchkit.
    """
    # We do not import SearchkitFilter to avoid circular imports. So we check
    # the filter by its name.
    return (
        admin.site.is_registered(model)
        and 'SearchkitFilter' in [getattr(f, '__name__', '') for f in admin.site._registry[model].list_filter]
    )


# TODO: Make modeltree parameters configurable.
class ModelTree(BaseModelTree):
    MAX_DEPTH = 3
    FOLLOW_ACROSS_APPS = True


def get_value_representation(value):
    """
    Get a string representation of a value for display in the admin.
    """
    if isinstance(value, list):
        return f'[{", ".join(get_value_representation(v) for v in value)}]'
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        template = Template("{{ value }}")
        return template.render(Context({'value': value}))
