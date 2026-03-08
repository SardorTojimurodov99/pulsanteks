from django.db import transaction
from django.utils import timezone

from orders.services import recalc_order_status
from .models import Batch, BatchStatus, Stage, StageLog


DEFAULT_BATCH_SIZE = 3000


@transaction.atomic
def create_batches_for_order(order, batch_size=DEFAULT_BATCH_SIZE):
    created = []
    for item in order.items.all():
        remaining = item.sheet_count
        counter = 1
        while remaining > 0:
            qty = min(batch_size, remaining)
            batch = Batch.objects.create(
                order=order,
                order_item=item,
                batch_no=f"{order.order_no}-{item.id}-{counter}",
                quantity=qty,
                stage=Stage.QABUL,
                status=BatchStatus.NEW,
            )
            StageLog.objects.create(batch=batch, from_stage="", to_stage=Stage.QABUL)
            created.append(batch)
            remaining -= qty
            counter += 1

    recalc_order_status(order)
    return created


@transaction.atomic
def start_batch(batch, user=None, note=""):
    if batch.status == BatchStatus.NEW:
        batch.status = BatchStatus.IN_PROGRESS
        batch.started_at = batch.started_at or timezone.now()
        batch.save(update_fields=["status", "started_at"])


@transaction.atomic
def advance_batch(batch, user=None, note=""):
    current = batch.stage
    nxt = batch.next_stage()

    if not nxt:
        return batch

    batch.status = BatchStatus.IN_PROGRESS
    batch.stage = nxt

    if nxt == Stage.OMBOR:
        batch.status = BatchStatus.DONE
        batch.finished_at = timezone.now()

    if nxt == Stage.JONATISH:
        batch.status = BatchStatus.SHIPPED

    batch.save(update_fields=["stage", "status", "finished_at"])
    StageLog.objects.create(
        batch=batch,
        from_stage=current,
        to_stage=nxt,
        changed_by=user,
        note=note,
    )
    recalc_order_status(batch.order)
    return batch