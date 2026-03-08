from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Batch, Stage
from .services import advance_batch


GROUP_STAGE_MAP = {
    "RANG_TAYYORLOVCHI": Stage.RANG_TAYYORLASH,
    "QUYUVCHI": Stage.QUYISH,
    "APPARATCHI": Stage.APPARAT,
    "PALIROFKACHI": Stage.PALIROFKA,
    "SARTIROVKACHI": Stage.SARTIROVKA,
    "OMBORCHI": Stage.OMBOR,
    "JONATUVCHI": Stage.JONATISH,
}


def get_user_stage(user):
    if user.is_superuser:
        return None

    group_names = set(user.groups.values_list("name", flat=True))

    for group_name, stage in GROUP_STAGE_MAP.items():
        if group_name in group_names:
            return stage

    return None


@login_required
def worker_dashboard(request):
    user_stage = get_user_stage(request.user)

    if request.user.is_superuser:
        batches = Batch.objects.select_related("order", "order_item").all().order_by("stage", "id")
    else:
        if not user_stage:
            messages.error(request, "Sizga worker roli biriktirilmagan.")
            return render(request, "production/worker_dashboard.html", {
                "batches": [],
                "user_stage": None,
            })

        batches = (
            Batch.objects.select_related("order", "order_item")
            .filter(stage=user_stage)
            .order_by("id")
        )

    return render(request, "production/worker_dashboard.html", {
        "batches": batches,
        "user_stage": user_stage,
    })


@login_required
def worker_batch_detail(request, pk):
    batch = get_object_or_404(
        Batch.objects.select_related("order", "order_item").prefetch_related("logs"),
        pk=pk
    )

    user_stage = get_user_stage(request.user)

    if not request.user.is_superuser:
        if not user_stage:
            messages.error(request, "Sizga worker roli biriktirilmagan.")
            return redirect("worker_dashboard")

        if batch.stage != user_stage:
            messages.error(request, "Bu batch sizning bo‘limingizga tegishli emas.")
            return redirect("worker_dashboard")

    return render(request, "production/worker_batch_detail.html", {
        "batch": batch,
        "user_stage": user_stage,
    })


@login_required
def worker_done(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    user_stage = get_user_stage(request.user)

    if request.method != "POST":
        return redirect("worker_batch_detail", pk=batch.pk)

    if not request.user.is_superuser:
        if not user_stage:
            messages.error(request, "Sizga worker roli biriktirilmagan.")
            return redirect("worker_dashboard")

        if batch.stage != user_stage:
            messages.error(request, "Bu batch sizning bo‘limingizga tegishli emas.")
            return redirect("worker_dashboard")

    note = request.POST.get("note", "").strip()
    advance_batch(batch, user=request.user, note=note)
    messages.success(request, "Batch keyingi bosqichga o‘tkazildi.")
    return redirect("worker_dashboard")