from django.contrib import admin

from .models import Batch, Machine, MachineAssignment, MachineBreakdown, StageLog


class StageLogInline(admin.TabularInline):
    model = StageLog
    extra = 0
    readonly_fields = ("from_stage", "to_stage", "changed_by", "note", "changed_at")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_no", "order", "quantity", "unit_type", "source_stage", "stage", "status", "is_repeat")
    list_filter = ("unit_type", "source_stage", "stage", "status", "is_repeat")
    search_fields = ("batch_no", "order__order_no", "order__customer_name")
    inlines = [StageLogInline]


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("code", "department", "status", "is_active")
    list_filter = ("department", "status", "is_active")


@admin.register(MachineAssignment)
class MachineAssignmentAdmin(admin.ModelAdmin):
    list_display = ("machine", "batch", "started_at", "paused_at", "finished_at", "is_active")


@admin.register(MachineBreakdown)
class MachineBreakdownAdmin(admin.ModelAdmin):
    list_display = ("machine", "batch", "status", "reported_at", "accepted_at", "fixed_at")
    list_filter = ("status", "machine__department")
