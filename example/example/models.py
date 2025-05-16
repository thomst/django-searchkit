from django.db import models


class ModelA(models.Model):
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    float = models.FloatField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    datetime = models.DateTimeField()


class ModelB(models.Model):
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    float = models.FloatField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    datetime = models.DateTimeField()
    model_a = models.ForeignKey(ModelA, on_delete=models.CASCADE)
