from django.contrib import admin
from .models import Shipment, ShipmentItem


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 1


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("shipment_no", "customer_name", "shipped_at")
    search_fields = ("shipment_no", "customer_name")
    inlines = [ShipmentItemInline]


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ("shipment", "warehouse_lot", "quantity")