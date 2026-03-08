from django.conf import settings
from django.db import models
from orders.models import LaserType


class Stage(models.TextChoices):
    QABUL = "QABUL", "Qabul"
    RANG_TAYYORLASH = "RANG_TAYYORLASH", "Rang tayyorlash"
    QUYISH = "QUYISH", "Quyuvchi"
    APPARAT = "APPARAT", "Apparatchi"
    PALIROFKA = "PALIROFKA", "Palirofkachi"
    SARTIROVKA = "SARTIROVKA", "Sartirofkachi"
    QAVAT = "QAVAT", "Qavat"
    LAZER = "LAZER", "Lazer"
    OMBOR = "OMBOR", "Ombor"
    JONATISH = "JONATISH", "Jo'natish"


class BatchStatus(models.TextChoices):
    NEW = "NEW", "Yangi"
    IN_PROGRESS = "IN_PROGRESS", "Jarayonda"
    DONE = "DONE", "Tayyor"
    WAREHOUSE = "WAREHOUSE", "Omborda"
    SHIPPED = "SHIPPED", "Jo'natilgan"
    HOLD = "HOLD", "To'xtatilgan"


class Batch(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="batches")
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.CASCADE, related_name="batches")
    batch_no = models.CharField(max_length=50, unique=True)
    quantity = models.PositiveIntegerField(verbose_name="Batch list soni")
    stage = models.CharField(max_length=30, choices=Stage.choices, default=Stage.QABUL)
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.batch_no

    def flow(self):
        flow = [
            Stage.QABUL,
            Stage.RANG_TAYYORLASH,
            Stage.QUYISH,
            Stage.APPARAT,
            Stage.PALIROFKA,
            Stage.SARTIROVKA,
        ]

        if self.order_item.is_coated:
            flow.append(Stage.QAVAT)

        if self.order_item.laser == LaserType.LASER:
            flow.append(Stage.LAZER)

        flow += [
            Stage.OMBOR,
            Stage.JONATISH,
        ]
        return flow

    def next_stage(self):
        flow = self.flow()
        try:
            idx = flow.index(self.stage)
        except ValueError:
            return None

        if idx + 1 < len(flow):
            return flow[idx + 1]
        return None


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

    def __str__(self):
        return f"{self.batch.batch_no}: {self.from_stage} -> {self.to_stage}"