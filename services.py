from django.db import transaction
from django.utils import timezone
from .models import Stage, StageLog, MachineStatus, Batch

def _flow_for_stage(order, current_stage: str):
    """Order flow ichidan batchning current_stage bo‘yicha next stage topadi."""
    flow = order.flow()  # order.finish ga qarab MATIVIY qo‘shadi
    try:
        i = flow.index(current_stage)
    except ValueError:
        i = 0
    return flow[min(i + 1, len(flow) - 1)]

@transaction.atomic
def mark_batch_done_and_advance(batch: Batch, note: str = ""):
    """
    1) batchni done qiladi
    2) agar mashinada bo‘lsa bo‘shatadi
    3) next stage ga o‘tkazadi
    4) log yozadi
    5) order.stage ni ham yangilab qo‘yadi (oddiy variant)
    """
    from_stage = batch.stage

    # batch done
    batch.is_done = True
    batch.save(update_fields=["is_done"])

    # agar mashina biriktirilgan bo‘lsa -> bo‘shatish
    if batch.machine_id:
        m = batch.machine
        m.status = MachineStatus.IDLE
        m.current_batch = None
        m.busy_since = None
        m.save(update_fields=["status", "current_batch", "busy_since"])

    # next stage
    to_stage = _flow_for_stage(batch.order, from_stage)

    batch.stage = to_stage
    batch.is_done = False
    batch.machine = None
    batch.save(update_fields=["stage", "is_done", "machine"])

    # order stage ham shu bosqichga (keyin “batchlar bo‘yicha umumiy stage”ni ham qilamiz)
    batch.order.stage = to_stage
    batch.order.save(update_fields=["stage"])

    StageLog.objects.create(
        order=batch.order,
        batch=batch,
        from_stage=from_stage,
        to_stage=to_stage,
        note=note or f"{from_stage} tugadi -> {to_stage}"
    )