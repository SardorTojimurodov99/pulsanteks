from django.db import transaction
from production.models import BatchStatus, Stage
from .models import WarehouseLot
from orders.services import recalc_order_status


@transaction.atomic
def receive_batch_to_warehouse(batch, note=""):
    lot, created = WarehouseLot.objects.get_or_create(
        batch=batch,
        defaults={
            "quantity": batch.quantity,
            "remaining_quantity": batch.quantity,
            "note": note,
        },
    )
    batch.stage = Stage.OMBOR
    batch.status = BatchStatus.WAREHOUSE
    batch.save(update_fields=["stage", "status"])
    recalc_order_status(batch.order)
    return lot