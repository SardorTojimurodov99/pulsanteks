from django.core.management.base import BaseCommand
from main.models import Machine, MachineStatus


class Command(BaseCommand):
    help = "Apparatlarni yaratadi: A1..A6, B1..B6, C1..C4, D1..D4"

    def handle(self, *args, **options):
        names = (
            [f"A{i}" for i in range(1, 7)] +
            [f"B{i}" for i in range(1, 7)] +
            [f"C{i}" for i in range(1, 5)] +
            [f"D{i}" for i in range(1, 5)]
        )
        created = 0
        for n in names:
            obj, is_created = Machine.objects.get_or_create(code=n, defaults={"status": MachineStatus.IDLE})
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"✅ Tayyor: {len(names)} ta. Yangi: {created} ta."))