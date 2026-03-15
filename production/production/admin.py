from django.contrib import admin
from .models import Batch, StageLog


class StageLogInline(admin.TabularInline):
    model = StageLog
    extra = 0
    readonly_fields = ("from_stage", "to_stage", "changed_by", "note", "changed_at")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_no", "order", "order_item", "quantity", "stage", "status", "created_at")
    list_filter = ("stage", "status")
    search_fields = ("batch_no", "order__order_no", "order__customer_name")
    inlines = [StageLogInline]


@admin.register(StageLog)
class StageLogAdmin(admin.ModelAdmin):
    list_display = ("batch", "from_stage", "to_stage", "changed_by", "changed_at")
    list_filter = ("to_stage", "changed_at")