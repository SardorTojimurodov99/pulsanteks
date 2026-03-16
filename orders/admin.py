from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    max_num = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_no",
        "customer_name",
        "order_date",
        "accepted_at",
        "current_stage",
        "status",
        "use_order_flow",
    )
    search_fields = ("order_no", "customer_name")
    list_filter = ("status", "current_stage", "accepted_at", "order_date")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "size",
        "primary_color",
        "material_type",
        "is_coated",
        "surface",
        "laser",
        "sheet_count",
        "button_count",
        "smala_kg",
        "thickness",
    )
    search_fields = (
        "order__order_no",
        "order__customer_name",
        "size",
        "primary_color",
        "secondary_color",
        "pantone",
    )
    list_filter = ("material_type", "is_coated", "surface", "laser")
