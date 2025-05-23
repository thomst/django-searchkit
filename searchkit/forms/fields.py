from django import forms
from django.utils.translation import gettext_lazy as _


class RangeWidget(forms.MultiWidget):
    def decompress(self, value):
        """The value should be already a list."""
        if value:
            return value
        else:
            return [None, None]


class BaseRangeField(forms.MultiValueField):
    incomplete_message = None
    field_type = None
    widget_type = None
    field_kwargs = dict()

    def __init__(self, **kwargs):
        error_messages = dict(incomplete=self.incomplete_message)
        widget = RangeWidget(widgets=[self.widget_type, self.widget_type])
        fields = (
            self.field_type(label=_('From'), **self.field_kwargs),
            self.field_type(label=_('To'), **self.field_kwargs),
        )
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )

    def compress(self, data_list):
        """We want the data list as data list."""
        return data_list


class IntegerRangeField(BaseRangeField):
    incomplete_message = _("Enter the first and the last number.")
    field_type = forms.IntegerField
    widget_type = forms.NumberInput


class DateRangeField(BaseRangeField):
    incomplete_message = _("Enter the first and the last date.")
    field_type = forms.DateField
    widget_type = forms.DateInput


class DateTimeRangeField(BaseRangeField):
    incomplete_message = _("Enter the first and the last datetime.")
    field_type = forms.DateTimeField
    widget_type = forms.DateTimeInput
