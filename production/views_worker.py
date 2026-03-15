from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Batch, Machine, MachineBreakdown, Stage, StageProgress
from .services import (
    accept_breakdown,
    accept_stage,
    fix_breakdown,
    finish_machine,
    finish_stage,
    pause_machine,
    report_machine_breakdown,
    start_machine,
)


GROUP_STAGE_MAP = {
    "RANG_TAYYORLOVCHI": Stage.RANG_TAYYORLASH,
    "QUYUVCHI": Stage.QUYISH,
    "APPARATCHI": Stage.APPARAT,
    "PALIROFKACHI": Stage.PALIROFKA,
    "SARTIROVKACHI": Stage.SARTIROVKA,
    "OMBORCHI": Stage.OMBOR,
    "JONATUVCHI": Stage.JONATISH,
}


STAGE_SEQUENCE = [
    Stage.RANG_TAYYORLASH,
    Stage.QUYISH,
    Stage.APPARAT,
    Stage.PALIROFKA,
    Stage.SARTIROVKA,
    Stage.OMBOR,
    Stage.JONATISH,
]


def get_stage_label(stage_value):
    for value, label in Stage.choices:
        if value == stage_value:
            return label
    return stage_value


def get_user_stages(user):

    if user.is_superuser:
        return None

    group_names = set(user.groups.values_list("name", flat=True))

    if "MASTER" in group_names:
        return None

    stages = []

    for group_name, stage in GROUP_STAGE_MAP.items():
        if group_name in group_names:
            stages.append(stage)

    return stages


@login_required
def worker_dashboard(request):

    allowed_stages = get_user_stages(request.user)
    requested_stage = request.GET.get("stage", "all")

    if allowed_stages is None:

        base_qs = Batch.objects.select_related("order", "order_item").all()

        if requested_stage == "all":
            batches = base_qs.order_by("stage", "id")
            current_stage = "all"
        else:

            if requested_stage not in STAGE_SEQUENCE:
                messages.error(request, "Noto‘g‘ri bo‘lim tanlandi.")
                return redirect("worker_dashboard")

            batches = base_qs.filter(stage=requested_stage).order_by("id")
            current_stage = requested_stage

        visible_stages = STAGE_SEQUENCE
        is_master = True
        no_role = False

    else:

        if not allowed_stages:

            batches = Batch.objects.none()
            visible_stages = []
            current_stage = None
            is_master = False
            no_role = True

            messages.error(request, "Sizga worker bo‘lim biriktirilmagan.")

        else:

            visible_stages = [s for s in STAGE_SEQUENCE if s in allowed_stages]

            if requested_stage == "all":

                batches = (
                    Batch.objects
                    .select_related("order", "order_item")
                    .filter(stage__in=visible_stages)
                    .order_by("stage", "id")
                )

                current_stage = "all"

            else:

                if requested_stage not in visible_stages:
                    messages.error(request, "Bu bo‘lim sizga biriktirilmagan.")
                    return redirect("worker_dashboard")

                batches = (
                    Batch.objects
                    .select_related("order", "order_item")
                    .filter(stage=requested_stage)
                    .order_by("id")
                )

                current_stage = requested_stage

            is_master = False
            no_role = False

    stage_tabs = []

    if is_master or visible_stages:
        stage_tabs.append({"value": "all", "label": "Barchasi"})

    for stage in visible_stages:
        stage_tabs.append({
            "value": stage,
            "label": get_stage_label(stage),
        })

    return render(request, "production/worker_dashboard.html", {
        "batches": batches,
        "allowed_stages": allowed_stages,
        "visible_stages": visible_stages,
        "stage_tabs": stage_tabs,
        "current_stage": current_stage,
        "is_master": is_master,
        "no_role": no_role,
    })


@login_required
def worker_batch_detail(request, pk):

    batch = get_object_or_404(
        Batch.objects
        .select_related("order", "order_item")
        .prefetch_related("logs", "progresses", "machine_assignments"),
        pk=pk
    )

    allowed_stages = get_user_stages(request.user)

    if allowed_stages is not None:

        if not allowed_stages:
            messages.error(request, "Sizga worker bo‘lim biriktirilmagan.")
            return redirect("worker_dashboard")

        if batch.stage not in allowed_stages:
            messages.error(request, "Bu batch sizning bo‘limingizga tegishli emas.")
            return redirect("worker_dashboard")

    current_progress, _ = StageProgress.objects.get_or_create(batch=batch, stage=batch.stage)

    active_assignments = (
        batch.machine_assignments
        .select_related("machine")
        .filter(is_active=True, is_finished=False)
    )

    machines = (
        Machine.objects
        .filter(is_active=True)
        .order_by("code")
        if batch.stage == Stage.APPARAT else []
    )

    return render(request, "production/worker_batch_detail.html", {
        "batch": batch,
        "current_progress": current_progress,
        "allowed_stages": allowed_stages,
        "machines": machines,
        "active_assignments": active_assignments,
    })


@login_required
def worker_accept(request, pk):

    batch = get_object_or_404(Batch, pk=pk)
    note = request.POST.get("note", "").strip()

    accept_stage(batch, user=request.user, note=note)

    messages.success(request, "Bosqich qabul qilindi.")
    return redirect("worker_batch_detail", pk=batch.pk)


@login_required
def worker_finish(request, pk):

    batch = get_object_or_404(Batch, pk=pk)
    note = request.POST.get("note", "").strip()

    finish_stage(batch, user=request.user, note=note)

    messages.success(request, "Bosqich tugatildi.")

    return redirect("worker_dashboard")


@login_required
def machine_panel(request):
    machines = (
        Machine.objects
        .filter(is_active=True)
        .prefetch_related("assignments__batch", "assignments__batch__order")
        .order_by("code")
    )

    grouped = {
        "A": [],
        "B": [],
        "C": [],
        "D": [],
    }

    for machine in machines:
        active_assignment = (
            machine.assignments
            .select_related("batch", "batch__order")
            .filter(is_active=True, is_finished=False)
            .first()
        )

        item = {
            "machine": machine,
            "active_assignment": active_assignment,
        }

        if machine.code.startswith("A"):
            grouped["A"].append(item)
        elif machine.code.startswith("B"):
            grouped["B"].append(item)
        elif machine.code.startswith("C"):
            grouped["C"].append(item)
        elif machine.code.startswith("D"):
            grouped["D"].append(item)

    return render(request, "production/machine_list.html", {
        "grouped": grouped,
    })


@login_required
def machine_detail(request, machine_id):

    machine = get_object_or_404(Machine, pk=machine_id)

    assignments = (
        machine.assignments
        .select_related("batch", "batch__order")
        .all()
    )

    active_assignment = (
        machine.assignments
        .select_related("batch", "batch__order")
        .filter(is_active=True, is_finished=False)
        .first()
    )

    available_batches = (
        Batch.objects
        .select_related("order", "order_item")
        .filter(stage=Stage.APPARAT)
        .order_by("id")
    )

    return render(request, "production/machine_detail.html", {
        "machine": machine,
        "assignments": assignments,
        "active_assignment": active_assignment,
        "available_batches": available_batches,
    })


@login_required
def machine_start(request, machine_id):

    machine = get_object_or_404(Machine, pk=machine_id)

    batch_id = request.POST.get("batch_id")
    note = request.POST.get("note", "").strip()

    batch = get_object_or_404(Batch, pk=batch_id)

    start_machine(batch, machine, user=request.user, note=note)

    messages.success(request, "Ish boshlandi.")

    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_pause(request, machine_id):

    machine = get_object_or_404(Machine, pk=machine_id)

    batch_id = request.POST.get("batch_id")
    note = request.POST.get("note", "").strip()

    batch = get_object_or_404(Batch, pk=batch_id)

    pause_machine(batch, machine, note=note)

    messages.warning(request, "Pauza qilindi.")

    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_finish(request, machine_id):

    machine = get_object_or_404(Machine, pk=machine_id)

    batch_id = request.POST.get("batch_id")
    note = request.POST.get("note", "").strip()

    batch = get_object_or_404(Batch, pk=batch_id)

    finish_machine(batch, machine, user=request.user, note=note)
    finish_stage(batch, user=request.user, note="Apparat tugatdi")

    messages.success(request, "Ish tugatildi.")

    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_broken(request, machine_id):

    machine = get_object_or_404(Machine, pk=machine_id)

    batch_id = request.POST.get("batch_id")
    reason = request.POST.get("reason", "").strip()
    note = request.POST.get("note", "").strip()

    batch = get_object_or_404(Batch, pk=batch_id)

    report_machine_breakdown(batch, machine, user=request.user, reason=reason, note=note)

    messages.error(request, "Apparat buzildi.")

    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def mechanic_dashboard(request):

    breakdowns = MachineBreakdown.objects.select_related(
        "machine",
        "batch",
        "batch__order"
    )

    return render(request, "production/mechanic_dashboard.html", {
        "breakdowns": breakdowns
    })


@login_required
def mechanic_accept(request, breakdown_id):

    breakdown = get_object_or_404(MachineBreakdown, pk=breakdown_id)

    note = request.POST.get("note", "").strip()

    accept_breakdown(breakdown, user=request.user, note=note)

    messages.success(request, "Mexanik qabul qildi.")

    return redirect("mechanic_dashboard")


@login_required
def mechanic_fix(request, breakdown_id):

    breakdown = get_object_or_404(MachineBreakdown, pk=breakdown_id)

    note = request.POST.get("note", "").strip()

    fix_breakdown(breakdown, user=request.user, note=note)

    messages.success(request, "Apparat tuzatildi.")

    return redirect("mechanic_dashboard")