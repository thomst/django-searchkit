from collections import OrderedDict
from picklefield.fields import PickledObjectField
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class Search(models.Model):
    name = models.CharField(_('Search name'), max_length=255)
    contenttype = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Model'))
    data = PickledObjectField(_('Serialized filter rule data'))
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'contenttype')

    def as_q(self):
        """
        Build a Q object from the serialized data.
        """
        q = Q()
        for data in self.data:
            new_q = Q(**{f'{data["field"]}__{data["operator"]}': data['value']})
            if data['negation']:
                new_q = ~new_q
            if data['logical_operator'] == 'and':
                q &= new_q
            elif data['logical_operator'] == 'or':
                q |= new_q
            elif data['logical_operator'] == 'xor':
                q ^= new_q
        return q
