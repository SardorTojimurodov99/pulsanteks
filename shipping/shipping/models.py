from django.core.exceptions import ValidationError
from django.db import models
from warehouse.models import WarehouseLot


class Shipment(models.Model):
    shipment_no = models.CharField(max_length=30, unique=True)
    customer_name = models.CharField(max_length=255)
    shipped_at = models.DateTimeField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-shipped_at", "-id"]

    def __str__(self):
        return self.shipment_no


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="items")
    warehouse_lot = models.ForeignKey(WarehouseLot, on_delete=models.PROTECT, related_name="shipment_items")
    quantity = models.PositiveIntegerField()

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Jo'natma soni 0 dan katta bo'lishi kerak.")
        if self.warehouse_lot and self.quantity > self.warehouse_lot.remaining_quantity:
            raise ValidationError("Ombordagi qoldiqdan ko'p jo'natib bo'lmaydi.")

    def __str__(self):
        return f"{self.shipment.shipment_no} / {self.quantity}"