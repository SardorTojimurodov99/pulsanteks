from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from production.models import Batch
from .models import WarehouseLot
from .services import receive_batch_to_warehouse


def warehouse_list(request):
    lots = WarehouseLot.objects.select_related("batch", "batch__order").all()
    return render(request, "warehouse/lot_list.html", {"lots": lots})


def receive_batch(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == "POST":
        receive_batch_to_warehouse(batch)
        messages.success(request, "Batch omborga qabul qilindi.")
    return redirect("warehouse_list")