from django.db import models


CHARS_CHOICES = (
    ('one', 'One'),
    ('two', 'Two'),
    ('three', 'Three'),
    ('four', 'Four'),
)
INTEGER_CHOICES = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
)


class ModelA(models.Model):
    boolean = models.BooleanField(null=True)
    chars = models.CharField(max_length=255)
    chars_choices = models.CharField(max_length=255, choices=CHARS_CHOICES)
    integer = models.IntegerField()
    integer_choices = models.IntegerField(choices=INTEGER_CHOICES)
    float = models.FloatField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    datetime = models.DateTimeField()
    model_b = models.OneToOneField('ModelB', on_delete=models.CASCADE, null=True)


class ModelB(models.Model):
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    float = models.FloatField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    datetime = models.DateTimeField()
    model_a = models.ForeignKey(ModelA, on_delete=models.CASCADE)
