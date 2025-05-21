from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


# Create your models here.
# TODO: Use pickled cleaned data with a char field.
class SearchkitSearch(models.Model):
    name = models.CharField(_('Search name'), max_length=255)
    contenttype = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Model'))
    data = models.JSONField(_('Raw data of a searchkit formset'))
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'contenttype')