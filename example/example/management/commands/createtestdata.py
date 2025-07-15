import random
import string
import uuid
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from example.models import ModelA, ModelB, ModelC, ModelD
from example.models import CHARS_CHOICES, INTEGER_CHOICES


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

        # Create ModelC instances
        modeld_list = []
        for i in range(100):
            modeld = ModelD.objects.create(
                chars=f"ModelD chars {i}",
                integer=random.randint(1, 100),
                date=timezone.now().date() - timedelta(days=random.randint(0, 1000)),
            )
            modeld_list.append(modeld)

        # Create ModelC instances
        modelc_list = []
        for i in range(10):
            modelc = ModelC.objects.create(
                boolean=random.choice([False, True]),
                chars=f"ModelC chars {i}",
                integer=random.randint(1, 100),
                date=timezone.now().date() - timedelta(days=random.randint(0, 1000)),
            )
            modelc_list.append(modelc)

        # Create ModelB instances
        modelb_list = []
        for i in range(500):
            modelb = ModelB.objects.create(
                chars=random.choice([f"ModelB chars {i}", None]),
                integer=random.choice([random.randint(1, 1000), None]),
                decimal=random.choice([Decimal(f"{random.uniform(1, 999):.2f}"), None]),
                date=random.choice([timezone.now().date() - timedelta(days=random.randint(0, 1000)), None]),
                datetime=random.choice([timezone.now() - timedelta(days=random.randint(0, 1000)), None]),
                model_c=random.choice(modelc_list),
            )
            modelb_list.append(modelb)

        # Create ModelA instances
        modela_list = []
        for i in range(1000):
            random_string = ''.join(random.choices(string.ascii_letters, k=6))
            random_choices = random.choices(string.ascii_letters, k=1000)
            random_choices = [f'{c}\n' if i % 60 == 59 else c for i, c in enumerate(random_choices)]
            random_text = ''.join(random_choices)
            model_a = ModelA.objects.create(
                boolean=random.choice([True, False, None]),
                chars=f"ModelA chars {i}",
                chars_choices=random.choice([c[0] for c in CHARS_CHOICES]),
                text=random_text,
                email=f"user{i}-{random_string}@example.com",
                url=f"https://example.com/{random_string}/{i}",
                uuid=uuid.uuid4(),
                integer=random.randint(1, 1000),
                big_integer=random.randint(1, 100000),
                integer_choices=random.choice([c[0] for c in INTEGER_CHOICES]),
                float=random.uniform(1, 1000),
                decimal=Decimal(f"{random.uniform(1, 999):.2f}"),
                date=timezone.now().date() - timedelta(days=random.randint(0, 1000)),
                time=(timezone.now() - timedelta(minutes=random.randint(0, 1440))).time(),
                datetime=timezone.now() - timedelta(days=random.randint(0, 1000)),
            )
            modela_list.append(model_a)

        random.shuffle(modela_list)
        random.shuffle(modelb_list)
        random.shuffle(modeld_list)

        for modela in modela_list:
            modelds = random.choices(modeld_list, k=random.choice(range(5)))
            modela.model_d.add(*modelds)

        while modelb_list:
            modela = modela_list.pop()
            modela.model_b = modelb_list.pop()
            modela.save()

        self.stdout.write(self.style.SUCCESS("Test data created for ModelA, ModelB, and ModelC!"))