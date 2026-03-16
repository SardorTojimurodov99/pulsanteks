from django.db import models

from production.models import Batch


class WarehouseLot(models.Model):
    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name="warehouse_lot")
    quantity = models.PositiveIntegerField(verbose_name="Qabul qilingan miqdor")
    shipped_quantity = models.PositiveIntegerField(default=0, verbose_name="Jo'natilgan miqdor")
    remaining_quantity = models.PositiveIntegerField(verbose_name="Qoldiq")
    received_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.batch.batch_no} / {self.remaining_quantity}"
