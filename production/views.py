from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .models import Batch
from .services import advance_batch
from accounts.utils import redirect_worker_only


def batch_list(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batches = Batch.objects.select_related("order", "order_item").all()
    return render(request, "production/batch_list.html", {"batches": batches})


def batch_detail(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batch = get_object_or_404(Batch.objects.select_related("order", "order_item"), pk=pk)
    return render(request, "production/batch_detail.html", {"batch": batch})


def batch_advance(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batch = get_object_or_404(Batch, pk=pk)
    if request.method == "POST":
        advance_batch(batch, user=request.user if request.user.is_authenticated else None)
        messages.success(request, "Batch keyingi bosqichga o'tdi.")
    return redirect("batch_detail", pk=batch.pk)