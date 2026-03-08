from django.contrib import admin
from .models import WarehouseLot


@admin.register(WarehouseLot)
class WarehouseLotAdmin(admin.ModelAdmin):
    list_display = ("batch", "quantity", "remaining_quantity", "received_at")
    search_fields = ("batch__batch_no", "batch__order__order_no")