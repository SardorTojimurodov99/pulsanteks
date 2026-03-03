from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html

from .models import (
    Color, Order, Batch, Machine,
    WashingMachine, WashingLoad, WashingLoadItem,
    PackingLot, Location, WarehouseLot,
    Shipment, ShipmentItem,
    Ticket, StageLog
)

admin.site.site_header = "Pulsanteks Zavod Paneli"
admin.site.site_title = "Pulsanteks"
admin.site.index_title = "Boshqaruv"


# =========================
# BASIC DICTIONARIES
# =========================
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name")
    ordering = ("name",)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("code", "status", "current_batch", "busy_since")
    list_filter = ("status",)
    search_fields = ("code",)
    ordering = ("code",)
    list_select_related = ("current_batch",)


# =========================
# INLINES
# =========================
class BatchInline(admin.TabularInline):
    """
    Batch modelida Order FK bo'lishi kerak:
      order = models.ForeignKey(Order, ...)
    """
    model = Batch
    fk_name = "order"          # <<<< MUHIM
    extra = 0
    show_change_link = True
    autocomplete_fields = ("machine",)
    fields = (
        "title",
        "kg_plan", "list_plan",
        "kg_done", "list_done",
        "stage",
        "machine",
        "is_done", "is_paused",
    )


class StageLogInline(admin.TabularInline):
    """
    StageLog modelida Order FK bo'lsa:
      order = models.ForeignKey(Order, ...)
    """
    model = StageLog
    fk_name = "order"          # <<<< MUHIM (StageLog’da order FK bo‘lsa)
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ("created_at",)
    fields = ("batch", "from_stage", "to_stage", "note", "created_at")
    autocomplete_fields = ("batch",)


# =========================
# ORDER / BATCH
# =========================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "size_mm",
        "color",
        "kg_plan",
        "list_plan",
        "finish",
        "laser",
        "stage",
        "created_at",
    )
    list_filter = ("finish", "laser", "stage", "color")
    search_fields = ("customer_name", "laser_text")
    autocomplete_fields = ("color",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("color",)

    inlines = [BatchInline, StageLogInline]


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "title",
        "kg_plan", "list_plan",
        "kg_done", "list_done",
        "stage",
        "machine",
        "is_done",
        "is_paused",
        "updated_at",
    )
    list_filter = ("stage", "is_done", "is_paused", "machine")
    search_fields = ("order__customer_name", "title")
    autocomplete_fields = ("order", "machine")
    ordering = ("-updated_at",)
    list_select_related = ("order", "machine")


# =========================
# WASHING
# =========================
@admin.register(WashingMachine)
class WashingMachineAdmin(admin.ModelAdmin):
    list_display = ("code",)
    search_fields = ("code",)
    ordering = ("code",)


class WashingLoadItemInline(admin.TabularInline):
    model = WashingLoadItem
    extra = 0
    autocomplete_fields = ("batch",)
    fields = ("batch",)
    show_change_link = True


@admin.register(WashingLoad)
class WashingLoadAdmin(admin.ModelAdmin):
    list_display = ("id", "machine", "started_at", "finished_at", "is_done")
    list_filter = ("machine", "is_done")
    date_hierarchy = "started_at"
    ordering = ("-started_at",)
    list_select_related = ("machine",)
    inlines = [WashingLoadItemInline]


# =========================
# PACKING / WAREHOUSE
# =========================
@admin.register(PackingLot)
class PackingLotAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "packs", "kg", "pcs", "created_at")
    search_fields = ("order__customer_name",)
    autocomplete_fields = ("order",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("order",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code",)
    search_fields = ("code",)
    ordering = ("code",)


@admin.register(WarehouseLot)
class WarehouseLotAdmin(admin.ModelAdmin):
    list_display = ("lot_code", "location", "packs_left", "kg_left", "pcs_left", "created_at")
    search_fields = ("lot_code", "location__code")
    autocomplete_fields = ("packing_lot", "location")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("location", "packing_lot")


# =========================
# SHIPMENT
# =========================
class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    autocomplete_fields = ("lot",)
    fields = ("lot", "packs", "pcs", "kg")
    show_change_link = True


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [ShipmentItemInline]


# =========================
# TICKETS
# =========================
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "machine", "status", "severity", "title", "opened_at", "closed_at")
    list_filter = ("status", "severity", "machine")
    search_fields = ("machine__code", "title", "comment")
    autocomplete_fields = ("machine",)
    ordering = ("-opened_at",)
    list_select_related = ("machine",)


# =========================
# STAGE LOGS
# =========================
@admin.register(StageLog)
class StageLogAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "batch", "from_stage", "to_stage", "note", "created_at")
    list_filter = ("to_stage",)
    search_fields = ("order__customer_name", "note")
    autocomplete_fields = ("order", "batch")
    ordering = ("-created_at",)
    list_select_related = ("order", "batch")