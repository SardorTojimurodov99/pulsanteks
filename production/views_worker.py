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


def get_user_stages(user):
    """
    User qaysi stage larni ko'ra olishini qaytaradi.
    Superuser yoki MASTER bo'lsa hamma stage larni qaytaradi.
    """
    if user.is_superuser:
        return None  # None = hamma stage

    group_names = set(user.groups.values_list("name", flat=True))

    if "MASTER" in group_names:
        return None  # hamma stage

    stages = []
    for group_name, stage in GROUP_STAGE_MAP.items():
        if group_name in group_names:
            stages.append(stage)

    return stages


@login_required
def worker_dashboard(request):
    allowed_stages = get_user_stages(request.user)

    if allowed_stages is None:
        # superuser yoki MASTER
        batches = Batch.objects.select_related("order", "order_item").all().order_by("stage", "id")
        is_master = True
    else:
        if not allowed_stages:
            messages.error(request, "Sizga hech qanday worker bo‘lim biriktirilmagan.")
            batches = Batch.objects.none()
        else:
            batches = (
                Batch.objects.select_related("order", "order_item")
                .filter(stage__in=allowed_stages)
                .order_by("stage", "id")
            )
        is_master = False

    return render(request, "production/worker_dashboard.html", {
        "batches": batches,
        "allowed_stages": allowed_stages,
        "is_master": is_master,
    })


@login_required
def worker_batch_detail(request, pk):
    batch = get_object_or_404(
        Batch.objects.select_related("order", "order_item").prefetch_related("logs"),
        pk=pk
    )

    allowed_stages = get_user_stages(request.user)

    if allowed_stages is not None:
        if not allowed_stages:
            messages.error(request, "Sizga hech qanday worker bo‘lim biriktirilmagan.")
            return redirect("worker_dashboard")

        if batch.stage not in allowed_stages:
            messages.error(request, "Bu batch sizning bo‘limingizga tegishli emas.")
            return redirect("worker_dashboard")

    return render(request, "production/worker_batch_detail.html", {
        "batch": batch,
        "allowed_stages": allowed_stages,
        "is_master": allowed_stages is None,
    })


@login_required
def worker_done(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    allowed_stages = get_user_stages(request.user)

    if request.method != "POST":
        return redirect("worker_batch_detail", pk=batch.pk)

    if allowed_stages is not None:
        if not allowed_stages:
            messages.error(request, "Sizga hech qanday worker bo‘lim biriktirilmagan.")
            return redirect("worker_dashboard")

        if batch.stage not in allowed_stages:
            messages.error(request, "Bu batch sizning bo‘limingizga tegishli emas.")
            return redirect("worker_dashboard")

    note = request.POST.get("note", "").strip()
    advance_batch(batch, user=request.user, note=note)
    messages.success(request, "Batch keyingi bosqichga o‘tkazildi.")
    return redirect("worker_dashboard")