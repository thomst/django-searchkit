from collections import OrderedDict
from picklefield.fields import PickledObjectField
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class Search(models.Model):
    name = models.CharField(_('Search name'), max_length=255)
    contenttype = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Model'))
    data = PickledObjectField(_('Serialized filter rule data'))
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'contenttype')

    def as_lookups(self):
        lookups = OrderedDict()
        for data in self.data:
            lookups[f'{data["field"]}__{data["operator"]}'] = data['value']
        return lookups
