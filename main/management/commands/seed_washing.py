from django.core.management.base import BaseCommand
from main.models import WashingMachine


class Command(BaseCommand):
    help = "Yuvish apparatlarini yaratadi: W1..W5"

    def handle(self, *args, **options):
        created = 0
        for i in range(1, 6):
            obj, is_created = WashingMachine.objects.get_or_create(code=f"W{i}")
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"✅ W1..W5 tayyor. Yangi: {created} ta."))