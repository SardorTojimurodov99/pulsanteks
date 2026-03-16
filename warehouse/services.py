from django.db import transaction

from production.models import BatchStatus, Stage

from .models import WarehouseLot


@transaction.atomic
def receive_batch_to_warehouse(batch, quantity, note=""):
    lot, _ = WarehouseLot.objects.get_or_create(
        batch=batch,
        defaults={
            "quantity": quantity,
            "remaining_quantity": quantity,
            "shipped_quantity": 0,
            "note": note,
        },
    )
    if lot.pk and lot.quantity != quantity:
        lot.quantity = quantity
        lot.remaining_quantity = max(quantity - lot.shipped_quantity, 0)
        lot.note = note
        lot.save(update_fields=["quantity", "remaining_quantity", "note"])

    batch.stage = Stage.OMBOR
    batch.status = BatchStatus.WAREHOUSE
    batch.save(update_fields=["stage", "status"])
    return lot
