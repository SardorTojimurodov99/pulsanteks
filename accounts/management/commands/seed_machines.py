from django.core.management.base import BaseCommand
from production.models import Machine

MACHINE_CODES = [
    "A1", "A2", "A3", "A4", "A5", "A6",
    "B1", "B2", "B3", "B4", "B5", "B6",
    "C1", "C2", "C3", "C4",
    "D1", "D2", "D3", "D4",
]


class Command(BaseCommand):
    help = "Apparatlarni yaratadi"

    def handle(self, *args, **options):
        for code in MACHINE_CODES:
            Machine.objects.get_or_create(code=code)
        self.stdout.write(self.style.SUCCESS("Apparatlar yaratildi."))
