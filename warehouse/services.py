from django.db import transaction
from .models import WarehouseLot


@transaction.atomic
def ensure_warehouse_lot(batch, note=""):
    lot, created = WarehouseLot.objects.get_or_create(
        batch=batch,
        defaults={
            "quantity": batch.quantity,
            "remaining_quantity": batch.quantity,
            "note": note,
        },
    )
    if not created:
        lot.quantity = batch.quantity
        lot.remaining_quantity = batch.quantity
        if note:
            lot.note = note
        lot.save(update_fields=["quantity", "remaining_quantity", "note"])
    return lot


@transaction.atomic
def receive_batch_to_warehouse(batch, user=None, note=""):
    # Omborga avtomatik tushadi, bu funksiya manual sync uchun qoldirildi.
    return ensure_warehouse_lot(batch, note=note)
