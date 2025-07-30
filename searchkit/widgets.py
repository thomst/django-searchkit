from django import forms


class RangeWidget(forms.MultiWidget):
    """
    Range widget based on the MultiWidget with two sub-widgets.
    """
    template_name = "searchkit/widgets/rangewidget.html"
    def decompress(self, value):
        # For an empty value return a list with two None values.
        if value:
            return value
        else:
            return [None, None]


class Select2Mixin:
    """
    Prevent the widget from rendering all choices but only initial values.
    """
    def optgroups(self, name, value, attr=None):
        """
        Return options based on the value passed in - ignoring the choices at all.
        """
        # FIXME: Should we check the value against the choices?
        options = [self.create_option(name, v, v, True, i) for i, v in enumerate(value)]
        return [(None, options, 0)]


class Select2(Select2Mixin, forms.Select):
    pass


class MultiSelect2(Select2Mixin, forms.SelectMultiple):
    pass