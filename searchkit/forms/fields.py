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
    def compress(self, data_list):
        """We want the data list as data list."""
        return data_list


class IntegerRangeField(BaseRangeField):
    def __init__(self, **kwargs):
        error_messages = {
            "incomplete": _("Enter the first and the last number."),
        }
        fields = (
            forms.IntegerField(label=_('From')),
            forms.IntegerField(label=_('To')),
        )
        widget = RangeWidget(widgets=[forms.NumberInput, forms.NumberInput])
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )


class DateRangeField(BaseRangeField):
    def __init__(self, **kwargs):
        error_messages = {
            "incomplete": _("Enter the first and the last date."),
        }
        fields = (
            forms.DateField(label=_('From')),
            forms.DateField(label=_('To')),
        )
        widget = RangeWidget(widgets=[forms.DateInput, forms.DateInput]),
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )


class DateTimeRangeField(BaseRangeField):
    def __init__(self, **kwargs):
        error_messages = {
            "incomplete": _("Enter the first and the last datetime."),
        }
        fields = (
            forms.DateTimeField(label=_('From')),
            forms.DateTimeField(label=_('To')),
        )
        widget = RangeWidget(widgets=[forms.DateTimeInput, forms.DateTimeInput]),
        super().__init__(
            fields=fields,
            widget=widget,
            error_messages=error_messages,
            require_all_fields=True,
            **kwargs
        )
