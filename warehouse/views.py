from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import redirect_worker_only
from production.models import Batch, Stage

from .models import WarehouseLot
from .services import receive_batch_to_warehouse



def warehouse_list(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked
    lots = WarehouseLot.objects.select_related("batch", "batch__order").all()
    available_batches = Batch.objects.select_related("order").filter(stage=Stage.OMBOR).exclude(status="SHIPPED")
    return render(request, "warehouse/lot_list.html", {"lots": lots, "available_batches": available_batches})



def receive_batch(request, batch_id):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked
    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == "POST":
        quantity = int(request.POST.get("quantity") or 0)
        note = request.POST.get("note", "")
        receive_batch_to_warehouse(batch, quantity=quantity, note=note)
        messages.success(request, "Batch omborga qabul qilindi.")
    return redirect("warehouse_list")
