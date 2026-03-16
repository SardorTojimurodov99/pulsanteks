from django.db import transaction

from orders.services import refresh_order_done_state
from production.models import BatchStatus, Stage

from .models import Shipment



def generate_shipment_no():
    last = Shipment.objects.order_by("-id").first()
    if not last:
        return "SHP-0001"
    try:
        num = int(last.shipment_no.split("-")[-1])
    except Exception:
        num = last.id
    return f"SHP-{num + 1:04d}"


@transaction.atomic
def apply_shipment(shipment):
    for item in shipment.items.select_related("warehouse_lot", "warehouse_lot__batch"):
        lot = item.warehouse_lot
        lot.shipped_quantity += item.quantity
        lot.remaining_quantity = max(lot.quantity - lot.shipped_quantity, 0)
        lot.save(update_fields=["shipped_quantity", "remaining_quantity"])

        batch = lot.batch
        batch.stage = Stage.JONATISH
        if lot.remaining_quantity == 0:
            batch.status = BatchStatus.SHIPPED
        batch.save(update_fields=["stage", "status"])
        refresh_order_done_state(batch.order)
