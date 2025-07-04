from django import forms


class RangeWidget(forms.MultiWidget):
    """
    Range widget based on the MultiWidget with two sub-widgets.
    """
    template_name = "django/forms/widgets/rangewidget.html"
    def decompress(self, value):
        # For an empty value return a list with two None values.
        if value:
            return value
        else:
            return [None, None]
