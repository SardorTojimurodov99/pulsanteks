from django.db import transaction
from django.utils import timezone

from .models import (
    BatchStatus,
    MachineAssignment,
    MachineBreakdown,
    MachineStatus,
    RepairStatus,
    Stage,
    StageLog,
    StageProgress,
)

DEFAULT_BATCH_SIZE = 3000


@transaction.atomic
def create_batches_for_order(order, batch_size=DEFAULT_BATCH_SIZE):
    from .models import Batch

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

            for stage in batch.flow():
                StageProgress.objects.get_or_create(batch=batch, stage=stage)

            created.append(batch)
            remaining -= qty
            counter += 1

    return created


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
        return batch

    batch.stage = nxt
    if nxt == Stage.OMBOR:
        batch.status = BatchStatus.WAREHOUSE
    elif nxt == Stage.JONATISH:
        batch.status = BatchStatus.SHIPPED
    else:
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
        batch=batch, machine=machine, is_active=True, is_finished=False
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
        batch=batch, machine=machine, is_active=True, is_finished=False
    ).first()

    if not assignment:
        return None

    assignment.paused_at = timezone.now()
    if note:
        assignment.note = note
    assignment.save(update_fields=["paused_at", "note"])

    machine.status = MachineStatus.PAUSED
    machine.save(update_fields=["status"])
    return assignment


@transaction.atomic
def finish_machine(batch, machine, user=None, note=""):
    assignment = MachineAssignment.objects.filter(
        batch=batch, machine=machine, is_active=True, is_finished=False
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
    assignment = MachineAssignment.objects.filter(
        batch=batch, machine=machine, is_active=True, is_finished=False
    ).first()

    if assignment:
        assignment.paused_at = timezone.now()
        if note:
            assignment.note = note
        assignment.save(update_fields=["paused_at", "note"])

    machine.status = MachineStatus.BROKEN
    machine.save(update_fields=["status"])

    breakdown = MachineBreakdown.objects.create(
        machine=machine,
        batch=batch,
        reported_by=user,
        reason=reason,
        note=note,
    )

    batch.status = BatchStatus.HOLD
    batch.save(update_fields=["status"])
    return breakdown


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
    if batch.status == BatchStatus.HOLD:
        batch.status = BatchStatus.IN_PROGRESS
        batch.save(update_fields=["status"])

    return breakdown