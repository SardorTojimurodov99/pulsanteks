from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_no",
        "accepted_at",
        "customer_name",
        "due_at",
        "created_at",
    )
    search_fields = ("order_no", "customer_name")
    list_filter = ("accepted_at", "due_at", "created_at")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "size",
        "color",
        "is_coated",
        "techik_count",
        "surface",
        "laser",
        "sheet_count",
        "button_count",
        "smala_kg",
    )
    search_fields = (
        "order__order_no",
        "order__customer_name",
        "size",
        "color",
        "coating_note",
        "laser_note",
    )
    list_filter = (
        "is_coated",
        "surface",
        "laser",
    )