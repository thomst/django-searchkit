# Generated by Django 5.2.4 on 2025-07-14 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chars', models.CharField(max_length=255)),
                ('integer', models.IntegerField()),
                ('date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='modela',
            name='model_d',
            field=models.ManyToManyField(to='example.modeld'),
        ),
    ]
