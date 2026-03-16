from django.core.management.base import BaseCommand

from production.models import Machine, MachineDepartment


APPARAT_CODES = [
    "A1", "A2", "A3", "A4", "A5", "A6",
    "B1", "B2", "B3", "B4", "B5", "B6",
    "C1", "C2", "C3", "C4",
    "D1", "D2", "D3", "D4",
]

PALIROFKA_CODES = ["P1", "P2", "P3", "P4", "P5", "P6"]


class Command(BaseCommand):
    help = "Apparat va palirofka apparatlarini yaratadi"

    def handle(self, *args, **options):
        for code in APPARAT_CODES:
            Machine.objects.get_or_create(code=code, defaults={"department": MachineDepartment.APPARAT})
        for code in PALIROFKA_CODES:
            Machine.objects.get_or_create(code=code, defaults={"department": MachineDepartment.PALIROFKA})
        self.stdout.write(self.style.SUCCESS("Apparatlar yaratildi."))
