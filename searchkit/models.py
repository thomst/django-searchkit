from picklefield.fields import PickledObjectField
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .utils import FieldPlan
from .utils import flatten_option_group_choices
from .utils import get_value_representation


class Search(models.Model):
    name = models.CharField(_('Search name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    contenttype = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Model'))
    data = PickledObjectField(_('Serialized filter rule data'))
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'contenttype')

    @property
    def details(self):
        """
        Get a detailed string representation of the search.
        """
        details = 'WHERE '
        for data in self.data:
            if data.get('logical_operator'):
                details += data["logical_operator"].upper() + ' '
            if data.get('negation'):
                details += 'NOT '

            field_plan = FieldPlan(self.contenttype.model_class(), initial=data)
            field_choices = flatten_option_group_choices(field_plan.get_field_lookup_choices())
            field_label = dict(field_choices).get(data['field'], data['field'])
            operator_choices = flatten_option_group_choices(field_plan.get_operator_choices(data['field']))
            operator_label = dict(operator_choices).get(data['operator'], data['operator'])
            value_repr = get_value_representation(data['value'])
            details += f'{field_label} | {operator_label} | {value_repr}\n'

        return details.strip()

    def as_q(self):
        """
        Build a Q object from the serialized data.
        """
        q = Q()
        for data in self.data:
            new_q = Q(**{f'{data["field"]}__{data["operator"]}': data['value']})

            # Negate the new Q object if negation is set.
            if data.get('negation'):
                new_q = ~new_q

            # Combine the new Q object with the existing one using the logical
            # operator or 'and' by default.
            operator = data.get('logical_operator') or 'and'
            if operator == 'and':
                q &= new_q
            elif operator == 'or':
                q |= new_q
            elif operator == 'xor':
                q ^= new_q

        return q
