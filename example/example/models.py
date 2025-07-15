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
    text = models.TextField()
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
    model_b = models.OneToOneField('ModelB', on_delete=models.CASCADE, null=True, blank=True)
    model_d = models.ManyToManyField('ModelD')


class ModelB(models.Model):
    chars = models.CharField(max_length=255, null=True, blank=True)
    integer = models.IntegerField(null=True, blank=True)
    decimal = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    model_c = models.ForeignKey('ModelC', on_delete=models.CASCADE)


class ModelC(models.Model):
    boolean = models.BooleanField(null=False, default=True)
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    date = models.DateField()


class ModelD(models.Model):
    chars = models.CharField(max_length=255)
    integer = models.IntegerField()
    date = models.DateField()
