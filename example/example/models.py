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
    email = models.EmailField()
    url = models.URLField()
    uuid = models.UUIDField()
    integer = models.IntegerField()
    big_integer = models.BigIntegerField()
    integer_choices = models.IntegerField(choices=INTEGER_CHOICES)
    float = models.FloatField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    time = models.TimeField()
    datetime = models.DateTimeField()
    model_b = models.OneToOneField('ModelB', on_delete=models.CASCADE, null=True)


class ModelB(models.Model):
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    datetime = models.DateTimeField()
    model_c = models.ForeignKey('ModelC', on_delete=models.CASCADE)


class ModelC(models.Model):
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    date = models.DateField()
