from django.db import transaction
from django.utils import timezone

from orders.models import OrderStatus
from orders.services import next_stage as next_order_stage, refresh_order_done_state

from .models import (
    Batch,
    BatchStatus,
    MachineAssignment,
    MachineBreakdown,
    MachineStatus,
    RepairStatus,
    Stage,
    StageLog,
    StageProgress,
    UnitType,
)


BATCH_CREATOR_STAGES = {Stage.RANG_TAYYORLASH, Stage.QUYISH, Stage.SARTIROVKA}


@transaction.atomic
def generate_batch_no(order):
    prefix = order.order_no
    last = order.batches.order_by("-id").first()
    if not last:
        return f"{prefix}-B1"
    try:
        num = int(last.batch_no.split("-B")[-1])
    except Exception:
        num = order.batches.count()
    return f"{prefix}-B{num + 1}"


@transaction.atomic
def ensure_batch_progresses(batch):
    for stage in Batch.stage_sequence():
        StageProgress.objects.get_or_create(batch=batch, stage=stage)


@transaction.atomic
def create_batch_from_order(order, user=None, quantity=0, is_repeat=False, note="", scrap_quantity=0, inspection_note=""):
    item = order.item
    if not item:
        raise ValueError("Zakaz tarkibi topilmadi.")

    source_stage = order.current_stage
    if source_stage not in BATCH_CREATOR_STAGES:
        raise ValueError("Bu bo'limda batch yaratib bo'lmaydi.")

    next_stage = next_order_stage(source_stage)
    if not next_stage:
        raise ValueError("Keyingi bosqich topilmadi.")

    unit_type = UnitType.BUTTON if source_stage == Stage.SARTIROVKA else UnitType.LIST

    if not is_repeat:
        if unit_type == UnitType.LIST and quantity > order.remaining_list_count:
            raise ValueError("Qolgan list sonidan ko'p batch yaratib bo'lmaydi.")
        if unit_type == UnitType.BUTTON and (quantity + scrap_quantity) > order.remaining_button_count:
            raise ValueError("Qolgan tugma sonidan ko'p batch yaratib bo'lmaydi.")

    batch = Batch.objects.create(
        order=order,
        order_item=item,
        batch_no=generate_batch_no(order),
        quantity=quantity,
        unit_type=unit_type,
        source_stage=source_stage,
        stage=next_stage,
        status=BatchStatus.NEW,
        is_repeat=is_repeat,
        scrap_quantity=scrap_quantity,
        inspection_note=inspection_note,
        note=note,
        created_by=user,
    )
    ensure_batch_progresses(batch)

    StageLog.objects.create(
        batch=batch,
        from_stage=source_stage,
        to_stage=next_stage,
        changed_by=user,
        note=f"Batch yaratildi. {note}".strip(),
    )

    if not is_repeat:
        if source_stage == Stage.SARTIROVKA:
            if order.remaining_button_count_for_stage(source_stage) == 0:
                order.current_stage = next_stage
                order.use_order_flow = False
                order.save(update_fields=["current_stage", "use_order_flow"])
        else:
            if order.remaining_list_count_for_stage(source_stage) == 0:
                order.current_stage = next_stage
                order.use_order_flow = False
                order.save(update_fields=["current_stage", "use_order_flow"])

    order.status = OrderStatus.RELEASED
    order.save(update_fields=["status"])
    return batch


@transaction.atomic
def accept_order_stage(order, user=None, note=""):
    order.status = OrderStatus.RELEASED
    order.use_order_flow = True
    order.save(update_fields=["status", "use_order_flow"])
    return order


@transaction.atomic
def finish_order_stage(order, user=None, note=""):
    nxt = next_order_stage(order.current_stage)
    if not nxt:
        order.status = OrderStatus.DONE
        order.use_order_flow = False
        order.save(update_fields=["status", "use_order_flow"])
        return order

    order.current_stage = nxt
    order.status = OrderStatus.RELEASED
    order.use_order_flow = True
    order.save(update_fields=["current_stage", "status", "use_order_flow"])
    return order


@transaction.atomic
def accept_stage(batch, user=None, note=""):
    progress, _ = StageProgress.objects.get_or_create(batch=batch, stage=batch.stage)
    if progress.accepted_at:
        return progress
    progress.accepted_at = timezone.now()
    progress.accepted_by = user
    if note:
        progress.note = note
    progress.save(update_fields=["accepted_at", "accepted_by", "note"])
    batch.status = BatchStatus.IN_PROGRESS
    batch.save(update_fields=["status"])
    return progress


@transaction.atomic
def finish_stage(batch, user=None, note=""):
    current_stage = batch.stage
    progress, _ = StageProgress.objects.get_or_create(batch=batch, stage=current_stage)
    if not progress.accepted_at:
        progress.accepted_at = timezone.now()
        progress.accepted_by = user
    progress.finished_at = timezone.now()
    progress.finished_by = user
    if note:
        progress.note = note
    progress.save()

    nxt = batch.next_stage()
    if not nxt:
        batch.status = BatchStatus.DONE
        batch.save(update_fields=["status"])
        refresh_order_done_state(batch.order)
        return batch

    batch.stage = nxt
    batch.status = BatchStatus.NEW
    batch.save(update_fields=["stage", "status"])

    StageLog.objects.create(
        batch=batch,
        from_stage=current_stage,
        to_stage=nxt,
        changed_by=user,
        note=note,
    )
    return batch


@transaction.atomic
def advance_batch(batch, user=None, note=""):
    return finish_stage(batch, user=user, note=note)


@transaction.atomic
def start_machine(batch, machine, user=None, note=""):
    assignment = MachineAssignment.objects.filter(
        batch=batch,
        machine=machine,
        is_active=True,
        is_finished=False,
    ).first()
    if assignment:
        if not assignment.started_at:
            assignment.started_at = timezone.now()
            assignment.started_by = user
        if note:
            assignment.note = note
        assignment.save()
    else:
        assignment = MachineAssignment.objects.create(
            batch=batch,
            machine=machine,
            started_at=timezone.now(),
            started_by=user,
            note=note,
        )

    machine.status = MachineStatus.RUNNING
    machine.save(update_fields=["status"])
    batch.status = BatchStatus.IN_PROGRESS
    batch.save(update_fields=["status"])
    return assignment


@transaction.atomic
def pause_machine(batch, machine, note=""):
    assignment = MachineAssignment.objects.filter(
        batch=batch,
        machine=machine,
        is_active=True,
        is_finished=False,
    ).first()
    if not assignment:
        return None
    assignment.paused_at = timezone.now()
    if note:
        assignment.note = note
    assignment.save(update_fields=["paused_at", "note"])
    machine.status = MachineStatus.PAUSED
    machine.save(update_fields=["status"])
    batch.status = BatchStatus.PAUSED
    batch.save(update_fields=["status"])
    return assignment


@transaction.atomic
def resume_machine(batch, machine, user=None, note=""):
    assignment = MachineAssignment.objects.filter(
        batch=batch,
        machine=machine,
        is_active=True,
        is_finished=False,
    ).first()
    if not assignment:
        return None
    assignment.resumed_at = timezone.now()
    if note:
        assignment.note = note
    assignment.save(update_fields=["resumed_at", "note"])
    machine.status = MachineStatus.RUNNING
    machine.save(update_fields=["status"])
    batch.status = BatchStatus.IN_PROGRESS
    batch.save(update_fields=["status"])
    return assignment


@transaction.atomic
def finish_machine(batch, machine, user=None, note=""):
    assignment = MachineAssignment.objects.filter(
        batch=batch,
        machine=machine,
        is_active=True,
        is_finished=False,
    ).first()
    if not assignment:
        assignment = MachineAssignment.objects.create(
            batch=batch,
            machine=machine,
            started_at=timezone.now(),
            started_by=user,
            finished_at=timezone.now(),
            finished_by=user,
            is_active=False,
            is_finished=True,
            note=note,
        )
    else:
        if not assignment.started_at:
            assignment.started_at = timezone.now()
            assignment.started_by = user
        assignment.finished_at = timezone.now()
        assignment.finished_by = user
        assignment.is_active = False
        assignment.is_finished = True
        if note:
            assignment.note = note
        assignment.save()

    machine.status = MachineStatus.IDLE
    machine.save(update_fields=["status"])
    return assignment


@transaction.atomic
def report_machine_breakdown(batch, machine, user=None, reason="", note=""):
    MachineAssignment.objects.filter(
        batch=batch,
        machine=machine,
        is_active=True,
        is_finished=False,
    ).update(paused_at=timezone.now())

    machine.status = MachineStatus.BROKEN
    machine.save(update_fields=["status"])
    batch.status = BatchStatus.HOLD
    batch.save(update_fields=["status"])

    return MachineBreakdown.objects.create(
        machine=machine,
        batch=batch,
        reported_by=user,
        reason=reason,
        note=note,
    )


@transaction.atomic
def accept_breakdown(breakdown, user=None, note=""):
    if breakdown.status == RepairStatus.REPORTED:
        breakdown.status = RepairStatus.ACCEPTED
        breakdown.accepted_at = timezone.now()
        breakdown.accepted_by = user
        if note:
            breakdown.note = note
        breakdown.save()
    return breakdown


@transaction.atomic
def fix_breakdown(breakdown, user=None, note=""):
    breakdown.status = RepairStatus.FIXED
    breakdown.fixed_at = timezone.now()
    breakdown.fixed_by = user
    if note:
        breakdown.note = note
    breakdown.save()

    machine = breakdown.machine
    machine.status = MachineStatus.IDLE
    machine.save(update_fields=["status"])

    batch = breakdown.batch
    batch.status = BatchStatus.PAUSED
    batch.save(update_fields=["status"])
    return breakdown
