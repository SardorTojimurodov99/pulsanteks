from django.conf import settings
from django.db import models


class Stage(models.TextChoices):
    RANG_TAYYORLASH = "RANG_TAYYORLASH", "Rang tayyorlash"
    QUYISH = "QUYISH", "Quyish"
    APPARAT = "APPARAT", "Apparat"
    PALIROFKA = "PALIROFKA", "Palirofka"
    SARTIROVKA = "SARTIROVKA", "Sartirovka"
    OMBOR = "OMBOR", "Ombor"
    JONATISH = "JONATISH", "Jo'natish"


class BatchStatus(models.TextChoices):
    NEW = "NEW", "Yangi"
    IN_PROGRESS = "IN_PROGRESS", "Jarayonda"
    PAUSED = "PAUSED", "Pauzada"
    HOLD = "HOLD", "To'xtatilgan"
    WAREHOUSE = "WAREHOUSE", "Omborda"
    SHIPPED = "SHIPPED", "Jo'natilgan"
    DONE = "DONE", "Tugagan"


class UnitType(models.TextChoices):
    LIST = "LIST", "List"
    BUTTON = "BUTTON", "Tugma"


class MachineDepartment(models.TextChoices):
    APPARAT = "APPARAT", "Apparat"
    PALIROFKA = "PALIROFKA", "Palirofka"


class MachineStatus(models.TextChoices):
    IDLE = "IDLE", "Bo'sh"
    RUNNING = "RUNNING", "Ishlayapti"
    PAUSED = "PAUSED", "Pauzada"
    BROKEN = "BROKEN", "Buzilgan"


class RepairStatus(models.TextChoices):
    REPORTED = "REPORTED", "Xabar berilgan"
    ACCEPTED = "ACCEPTED", "Qabul qilingan"
    FIXED = "FIXED", "Tuzatildi"


class Batch(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="batches")
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.CASCADE, related_name="batches")
    batch_no = models.CharField(max_length=50, unique=True)
    quantity = models.PositiveIntegerField(verbose_name="Miqdor")
    unit_type = models.CharField(max_length=10, choices=UnitType.choices, default=UnitType.LIST)
    source_stage = models.CharField(max_length=30, choices=Stage.choices)
    stage = models.CharField(max_length=30, choices=Stage.choices)
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.NEW)
    is_repeat = models.BooleanField(default=False, verbose_name="Takror batch")
    scrap_quantity = models.PositiveIntegerField(default=0, verbose_name="Brak soni")
    inspection_note = models.TextField(blank=True, verbose_name="Rang nazorati")
    note = models.TextField(blank=True, verbose_name="Izoh")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_batches",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.batch_no

    @staticmethod
    def stage_sequence():
        return [
            Stage.RANG_TAYYORLASH,
            Stage.QUYISH,
            Stage.APPARAT,
            Stage.PALIROFKA,
            Stage.SARTIROVKA,
            Stage.OMBOR,
            Stage.JONATISH,
        ]

    def next_stage(self):
        flow = self.stage_sequence()
        try:
            idx = flow.index(self.stage)
        except ValueError:
            return None
        if idx + 1 < len(flow):
            return flow[idx + 1]
        return None

    @property
    def department(self):
        if self.stage == Stage.PALIROFKA:
            return MachineDepartment.PALIROFKA
        return MachineDepartment.APPARAT


class StageLog(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="logs")
    from_stage = models.CharField(max_length=30, choices=Stage.choices, blank=True)
    to_stage = models.CharField(max_length=30, choices=Stage.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]


class StageProgress(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="progresses")
    stage = models.CharField(max_length=30, choices=Stage.choices)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_stage_progresses",
    )
    finished_at = models.DateTimeField(null=True, blank=True)
    finished_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="finished_stage_progresses",
    )
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
        unique_together = ("batch", "stage")

    @property
    def duration_minutes(self):
        if self.accepted_at and self.finished_at:
            delta = self.finished_at - self.accepted_at
            return int(delta.total_seconds() // 60)
        return None


class Machine(models.Model):
    code = models.CharField(max_length=10, unique=True)
    department = models.CharField(max_length=20, choices=MachineDepartment.choices, default=MachineDepartment.APPARAT)
    status = models.CharField(max_length=20, choices=MachineStatus.choices, default=MachineStatus.IDLE)
    is_active = models.BooleanField(default=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["department", "code"]

    def __str__(self):
        return self.code


class MachineAssignment(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="machine_assignments")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="assignments")
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    resumed_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="started_machine_assignments",
    )
    finished_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="finished_machine_assignments",
    )
    is_active = models.BooleanField(default=True)
    is_finished = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]

    @property
    def duration_minutes(self):
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            return int(delta.total_seconds() // 60)
        return None


class MachineBreakdown(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="breakdowns")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="breakdowns")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reported_breakdowns",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_breakdowns",
    )
    fixed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fixed_breakdowns",
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    fixed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=RepairStatus.choices, default=RepairStatus.REPORTED)
    reason = models.TextField(blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]
