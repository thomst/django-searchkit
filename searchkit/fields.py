from django import forms
from django.contrib.admin import widgets
from django.utils.translation import gettext_lazy as _


class RangeWidget(forms.MultiWidget):
    def decompress(self, value):
        """The value should be already a list."""
        if value:
            return value
        else:
            return [None, None]


class BaseRangeField(forms.MultiValueField):
    field_type = None
    widget_type = None
    error_message = _("Enter 'From' and 'To' value of the range.")
    default_error_messages = {
        "invalid": error_message,
        "incomplete": error_message,
    }

    def __init__(self, **kwargs):
        widget = RangeWidget(widgets=[self.widget_type(), self.widget_type()])
        fields = (self.field_type(), self.field_type())
        super().__init__(
            fields=fields,
            widget=widget,
            require_all_fields=True,
            **kwargs
        )

    def compress(self, data_list):
        """We want the data list as data list."""
        return data_list


class IntegerRangeField(BaseRangeField):
    field_type = forms.IntegerField
    widget_type = forms.NumberInput


class FloatRangeField(IntegerRangeField):
    field_type = forms.FloatField


class DecimalRangeField(IntegerRangeField):
    field_type = forms.DecimalField


class DateRangeField(BaseRangeField):
    field_type = forms.DateField
    widget_type = widgets.AdminDateWidget


class DateTimeRangeField(DateRangeField):
    field_type = forms.SplitDateTimeField
    widget_type = widgets.AdminSplitDateTime
