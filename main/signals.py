from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Batch, Machine, MachineStatus, StageLog, Stage, Ticket, TicketStatus


@receiver(pre_save, sender=Batch)
def _batch_pre_save(sender, instance: Batch, **kwargs):
    if not instance.pk:
        return
    old = Batch.objects.get(pk=instance.pk)

    instance._old_machine_id = old.machine_id
    instance._old_is_done = old.is_done
    instance._old_stage = old.stage


@receiver(post_save, sender=Batch)
def _batch_post_save(sender, instance: Batch, created, **kwargs):
    # 1) Apparatta BUSY/IDLE
    if instance.machine_id:
        m = instance.machine
        if not instance.is_done and not instance.is_paused:
            if m.status != MachineStatus.BUSY or m.current_batch_id != instance.id:
                m.status = MachineStatus.BUSY
                m.current_batch = instance
                m.busy_since = m.busy_since or timezone.now()
                m.save(update_fields=["status", "current_batch", "busy_since"])
        else:
            # done/paused bo'lsa, apparatda boshqa aktiv batch bormi?
            has_active = Batch.objects.filter(machine=m, is_done=False, is_paused=False).exists()
            if not has_active:
                m.status = MachineStatus.IDLE
                m.current_batch = None
                m.busy_since = None
                m.save(update_fields=["status", "current_batch", "busy_since"])

    # 2) Order stage avtomatik: agar order.stage dagi batchlar hammasi done bo'lsa -> next_stage
    order = instance.order
    cur = order.stage
    cur_batches = order.batches.filter(stage=cur)
    if cur_batches.exists() and not cur_batches.filter(is_done=False).exists():
        new_stage = order.next_stage()
        if new_stage != cur:
            order.stage = new_stage
            order.save(update_fields=["stage"])
            StageLog.objects.create(order=order, batch=None, from_stage=cur, to_stage=new_stage, note="Avto o'tdi (batchlar tugadi)")


@receiver(pre_save, sender=Ticket)
def _ticket_pre_save(sender, instance: Ticket, **kwargs):
    if not instance.pk:
        return
    old = Ticket.objects.get(pk=instance.pk)
    instance._old_status = old.status


@receiver(post_save, sender=Ticket)
def _ticket_post_save(sender, instance: Ticket, created, **kwargs):
    # Ticket OPEN/IN_PROGRESS bo'lsa -> machine BROKEN
    if instance.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
        if instance.machine.status != MachineStatus.BROKEN:
            instance.machine.status = MachineStatus.BROKEN
            instance.machine.save(update_fields=["status"])

        # Shu apparatdagi batchlarni PAUSE qilish
        Batch.objects.filter(machine=instance.machine, is_done=False).update(is_paused=True)

    # Ticket DONE bo'lsa -> machine IDLE (agar aktiv batch qolmagan bo'lsa)
    if instance.status == TicketStatus.DONE:
        has_active = Batch.objects.filter(machine=instance.machine, is_done=False, is_paused=False).exists()
        if not has_active:
            instance.machine.status = MachineStatus.IDLE
            instance.machine.current_batch = None
            instance.machine.busy_since = None
            instance.machine.save(update_fields=["status", "current_batch", "busy_since"])