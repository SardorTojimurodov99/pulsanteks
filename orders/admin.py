from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ("smala_kg",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_no",
        "accepted_at",
        "customer_name",
        "due_at",
        "status",
        "total_sheets",
        "total_smala_kg",
    )
    list_filter = ("status", "accepted_at", "due_at")
    search_fields = ("order_no", "customer_name")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "size",
        "color",
        "coating",
        "surface",
        "laser",
        "sheet_count",
        "kg_per_sheet",
        "smala_kg",
    )
    list_filter = ("coating", "surface", "laser")
    search_fields = ("order__order_no", "order__customer_name", "size", "color")