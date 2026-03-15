from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import redirect_worker_only
from .forms import BatchForm
from .models import Batch
from .services import advance_batch, initialize_batch_tracking
from orders.models import Order, OrderItem


def batch_list(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batches = Batch.objects.select_related("order", "order_item").all().order_by("-id")
    return render(request, "production/batch_list.html", {"batches": batches})


def batch_detail(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batch = get_object_or_404(
        Batch.objects.select_related("order", "order_item").prefetch_related("logs", "progresses"),
        pk=pk,
    )
    return render(request, "production/batch_detail.html", {"batch": batch})


@login_required
def batch_create(request):
    order_id = request.GET.get("order") or request.POST.get("order")
    item_id = request.GET.get("item") or request.POST.get("order_item")

    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            initialize_batch_tracking(batch, initial_stage=batch.stage, changed_by=request.user, note="Batch qo'lda yaratildi")
            messages.success(request, "Batch yaratildi.")
            return redirect("batch_detail", pk=batch.pk)
    else:
        initial = {}
        if order_id:
            initial["order"] = order_id
        if item_id:
            initial["order_item"] = item_id
        form = BatchForm(initial=initial)

    return render(request, "production/batch_form.html", {"form": form, "title": "Batch yaratish"})


def batch_advance(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    batch = get_object_or_404(Batch, pk=pk)
    if request.method == "POST":
        advance_batch(batch, user=request.user if request.user.is_authenticated else None)
        messages.success(request, "Batch keyingi bosqichga o'tdi.")
    return redirect("batch_detail", pk=batch.pk)
