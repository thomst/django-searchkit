from django.contrib import admin


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
