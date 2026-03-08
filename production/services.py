from django.db import transaction
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

            StageLog.objects.create(
                batch=batch,
                from_stage="",
                to_stage=Stage.QABUL,
            )

            created.append(batch)
            remaining -= qty
            counter += 1

    return created


@transaction.atomic
def advance_batch(batch, user=None, note=""):
    current = batch.stage
    nxt = batch.next_stage()

    if not nxt:
        return batch

    batch.stage = nxt

    if nxt == Stage.JONATISH:
        batch.status = BatchStatus.SHIPPED
    elif nxt == Stage.OMBOR:
        batch.status = BatchStatus.WAREHOUSE
    else:
        batch.status = BatchStatus.IN_PROGRESS

    batch.save(update_fields=["stage", "status"])

    StageLog.objects.create(
        batch=batch,
        from_stage=current,
        to_stage=nxt,
        changed_by=user,
        note=note,
    )

    return batch