from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from production.models import Batch
from .models import WarehouseLot
from .services import receive_batch_to_warehouse
from accounts.utils import redirect_worker_only


def warehouse_list(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    lots = WarehouseLot.objects.select_related("batch", "batch__order").all()
    return render(request, "warehouse/lot_list.html", {"lots": lots})


def receive_batch(request, batch_id):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == "POST":
        receive_batch_to_warehouse(batch)
        messages.success(request, "Batch omborga qabul qilindi.")
    return redirect("warehouse_list")