import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from example.models import ModelA, ModelB, CHARS_CHOICES, INTEGER_CHOICES


class Command(BaseCommand):
    help = 'Generate test data for ModelA and ModelB'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating test data...")

        # Create a superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created successfully!"))
        else:
            self.stdout.write(self.style.WARNING("Superuser 'admin' already exists."))

        # Generate test data for ModelA
        model_a_instances = []
        for i in range(10):
            model_a = ModelA.objects.create(
                boolean=random.choice([None, True, False]),
                chars=f"ModelA_Chars_{i}",
                chars_choices=random.choice([c[0] for c in CHARS_CHOICES]),
                integer=random.randint(1, 100),
                integer_choices=random.choice([c[0] for c in INTEGER_CHOICES]),
                float=random.uniform(1.0, 100.0),
                decimal=Decimal(f"{random.randint(1, 100)}.{random.randint(0, 99)}"),
                date=timezone.now().date() - timedelta(days=random.randint(0, 365)),  # Use timezone.now()
                datetime=timezone.now() - timedelta(days=random.randint(0, 365))  # Use timezone.now()
            )
            model_a_instances.append(model_a)

        # Generate test data for ModelB
        model_b_instances = []
        for i in range(10):
            model_b = ModelB.objects.create(
                chars=f"ModelB_Chars_{i}",
                integer=random.randint(1, 100),
                float=random.uniform(1.0, 100.0),
                decimal=Decimal(f"{random.randint(1, 100)}.{random.randint(0, 99)}"),
                date=timezone.now().date() - timedelta(days=random.randint(0, 365)),  # Use timezone.now()
                datetime=timezone.now() - timedelta(days=random.randint(0, 365)),  # Use timezone.now()
                model_a=random.choice(model_a_instances)
            )
            model_b_instances.append(model_b)

        # Add modela -> modelb relation.
        for index, model_a in enumerate(model_a_instances):
            model_a.model_b = model_b_instances[index]
            model_a.save()

        self.stdout.write(self.style.SUCCESS("Test data created successfully!"))