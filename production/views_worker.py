from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Order, OrderStatus

from .forms import BatchCreateForm
from .models import Batch, BatchStatus, Machine, MachineBreakdown, MachineDepartment, Stage, StageProgress
from .services import (
    accept_breakdown,
    accept_order_stage,
    accept_stage,
    create_batch_from_order,
    finish_machine,
    finish_order_stage,
    finish_stage,
    fix_breakdown,
    pause_machine,
    report_machine_breakdown,
    resume_machine,
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

BATCH_CREATOR_STAGES = {Stage.RANG_TAYYORLASH, Stage.QUYISH, Stage.SARTIROVKA}


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


def get_machine_rows_for_stage(stage_value):
    if stage_value == Stage.APPARAT:
        qs = Machine.objects.filter(is_active=True, department=MachineDepartment.APPARAT).order_by("code")
        title = "Apparatlar"
    elif stage_value == Stage.PALIROFKA:
        qs = Machine.objects.filter(is_active=True, department=MachineDepartment.PALIROFKA).order_by("code")
        title = "Palirofka apparatlari"
    else:
        return [], ""

    rows = []
    for machine in qs:
        active_assignments = list(machine.assignments.select_related("batch", "batch__order", "order").filter(is_active=True, is_finished=False))
        rows.append({
            "machine": machine,
            "active_assignments": active_assignments,
            "active_count": len(active_assignments),
            "remaining_capacity": max(machine.capacity - len(active_assignments), 0),
        })
    return rows, title


@login_required
def worker_dashboard(request):
    allowed_stages = get_user_stages(request.user)
    requested_stage = request.GET.get("stage", "all")

    if allowed_stages is None:
        visible_stages = STAGE_SEQUENCE
        is_master = True
        no_role = False
    else:
        visible_stages = [s for s in STAGE_SEQUENCE if s in allowed_stages]
        is_master = False
        no_role = not visible_stages

    if requested_stage == "all":
        order_qs = Order.objects.filter(status=OrderStatus.RELEASED, use_order_flow=True)
        batch_qs = Batch.objects.select_related("order", "order_item").all()
        if visible_stages:
            order_qs = order_qs.filter(current_stage__in=visible_stages)
            batch_qs = batch_qs.filter(stage__in=visible_stages)
    else:
        order_qs = Order.objects.filter(status=OrderStatus.RELEASED, use_order_flow=True, current_stage=requested_stage)
        batch_qs = Batch.objects.select_related("order", "order_item").filter(stage=requested_stage)

    stage_tabs = [{"value": "all", "label": "Barchasi"}] if (is_master or visible_stages) else []
    for stage in visible_stages:
        stage_tabs.append({"value": stage, "label": get_stage_label(stage)})

    machine_rows = []
    machine_title = ""
    if requested_stage in (Stage.APPARAT, Stage.PALIROFKA):
        machine_rows, machine_title = get_machine_rows_for_stage(requested_stage)

    return render(request, "production/worker_dashboard.html", {
        "orders": order_qs.prefetch_related("items") if not no_role else Order.objects.none(),
        "batches": batch_qs if not no_role else Batch.objects.none(),
        "stage_tabs": stage_tabs,
        "current_stage": requested_stage,
        "is_master": is_master,
        "no_role": no_role,
        "machine_rows": machine_rows,
        "machine_title": machine_title,
    })


@login_required
def worker_order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items", "batches"), pk=pk)
    allowed_stages = get_user_stages(request.user)
    if allowed_stages is not None and order.current_stage not in allowed_stages:
        messages.error(request, "Bu zakaz sizning bo'limingizga tegishli emas.")
        return redirect("worker_dashboard")

    batch_form = None
    if order.current_stage in BATCH_CREATOR_STAGES:
        batch_form = BatchCreateForm(order=order, stage=order.current_stage)

    return render(request, "production/worker_order_detail.html", {
        "order": order,
        "item": order.item,
        "batch_form": batch_form,
    })


@login_required
def worker_order_accept(request, pk):
    order = get_object_or_404(Order, pk=pk)
    note = request.POST.get("note", "").strip()
    accept_order_stage(order, user=request.user, note=note)
    messages.success(request, "Zakaz qabul qilindi.")
    return redirect("worker_order_detail", pk=order.pk)


@login_required
def worker_order_finish(request, pk):
    order = get_object_or_404(Order, pk=pk)
    note = request.POST.get("note", "").strip()
    finish_order_stage(order, user=request.user, note=note)
    messages.success(request, "Zakaz keyingi bosqichga o'tdi.")
    return redirect("worker_dashboard")


@login_required
def worker_create_batch(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    if request.method != "POST":
        return redirect("worker_order_detail", pk=order.pk)

    form = BatchCreateForm(request.POST, order=order, stage=order.current_stage)
    if form.is_valid():
        batch = create_batch_from_order(
            order,
            user=request.user,
            quantity=form.cleaned_data["quantity"],
            is_repeat=form.cleaned_data.get("is_repeat", False),
            note=form.cleaned_data.get("note", ""),
            scrap_quantity=form.cleaned_data.get("scrap_quantity") or 0,
            inspection_note=form.cleaned_data.get("inspection_note", ""),
        )
        messages.success(request, f"Batch yaratildi: {batch.batch_no}")
        return redirect("worker_order_detail", pk=order.pk)

    return render(request, "production/worker_order_detail.html", {
        "order": order,
        "item": order.item,
        "batch_form": form,
    })


@login_required
def worker_batch_detail(request, pk):
    batch = get_object_or_404(
        Batch.objects.select_related("order", "order_item").prefetch_related("logs", "progresses", "machine_assignments"),
        pk=pk,
    )
    current_progress, _ = StageProgress.objects.get_or_create(batch=batch, stage=batch.stage)
    return render(request, "production/worker_batch_detail.html", {
        "batch": batch,
        "current_progress": current_progress,
    })


@login_required
def worker_accept(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    note = request.POST.get("note", "").strip()
    accept_stage(batch, user=request.user, note=note)
    messages.success(request, "Batch qabul qilindi.")
    return redirect("worker_batch_detail", pk=batch.pk)


@login_required
def worker_finish(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    note = request.POST.get("note", "").strip()
    finish_stage(batch, user=request.user, note=note)
    messages.success(request, "Batch keyingi bosqichga o'tdi.")
    return redirect("worker_dashboard")


@login_required
def machine_panel(request):
    machines = Machine.objects.filter(is_active=True).order_by("department", "code")
    grouped = {"A": [], "B": [], "C": [], "D": [], "P": []}
    for machine in machines:
        active_assignments = list(machine.assignments.select_related("batch", "batch__order", "order").filter(is_active=True, is_finished=False))
        item = {
            "machine": machine,
            "active_assignments": active_assignments,
            "active_count": len(active_assignments),
            "remaining_capacity": max(machine.capacity - len(active_assignments), 0),
        }
        if machine.department == MachineDepartment.PALIROFKA:
            grouped["P"].append(item)
        elif machine.code.startswith("A"):
            grouped["A"].append(item)
        elif machine.code.startswith("B"):
            grouped["B"].append(item)
        elif machine.code.startswith("C"):
            grouped["C"].append(item)
        elif machine.code.startswith("D"):
            grouped["D"].append(item)
    return render(request, "production/machine_list.html", {"grouped": grouped})


@login_required
def machine_detail(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    active_assignments = list(machine.assignments.select_related("batch", "batch__order", "order").filter(is_active=True, is_finished=False))
    assignments = machine.assignments.select_related("batch", "batch__order", "order").all()
    available_batches = Batch.objects.select_related("order", "order_item").filter(stage=machine.department, status__in=[BatchStatus.NEW, BatchStatus.PAUSED, BatchStatus.IN_PROGRESS]).order_by("-id")
    available_orders = Order.objects.filter(status=OrderStatus.RELEASED, use_order_flow=True, current_stage=machine.department).order_by("-id")
    return render(request, "production/machine_detail.html", {
        "machine": machine,
        "active_assignments": active_assignments,
        "assignments": assignments,
        "available_batches": available_batches,
        "available_orders": available_orders,
        "active_count": len(active_assignments),
        "remaining_capacity": max(machine.capacity - len(active_assignments), 0),
    })


@login_required
def machine_start(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    work_type = request.POST.get("work_type", "batch")
    note = request.POST.get("note", "").strip()
    try:
        if work_type == "order":
            order = get_object_or_404(Order, pk=request.POST.get("order_id"))
            start_machine(machine=machine, order=order, user=request.user, note=note)
        else:
            batch = get_object_or_404(Batch, pk=request.POST.get("batch_id"))
            start_machine(machine=machine, batch=batch, user=request.user, note=note)
        messages.success(request, "Ish boshlandi.")
    except Exception as exc:
        messages.error(request, str(exc))
    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_pause(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    work_type = request.POST.get("work_type", "batch")
    note = request.POST.get("note", "").strip()
    if work_type == "order":
        order = get_object_or_404(Order, pk=request.POST.get("order_id"))
        pause_machine(machine=machine, order=order, note=note)
    else:
        batch = get_object_or_404(Batch, pk=request.POST.get("batch_id"))
        pause_machine(machine=machine, batch=batch, note=note)
    messages.warning(request, "Pauza qilindi.")
    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_resume(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    work_type = request.POST.get("work_type", "batch")
    note = request.POST.get("note", "").strip()
    if work_type == "order":
        order = get_object_or_404(Order, pk=request.POST.get("order_id"))
        resume_machine(machine=machine, order=order, user=request.user, note=note)
    else:
        batch = get_object_or_404(Batch, pk=request.POST.get("batch_id"))
        resume_machine(machine=machine, batch=batch, user=request.user, note=note)
    messages.success(request, "Ish davom ettirildi.")
    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_finish(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    work_type = request.POST.get("work_type", "batch")
    note = request.POST.get("note", "").strip()
    if work_type == "order":
        order = get_object_or_404(Order, pk=request.POST.get("order_id"))
        finish_machine(machine=machine, order=order, user=request.user, note=note)
        finish_order_stage(order, user=request.user, note=note)
    else:
        batch = get_object_or_404(Batch, pk=request.POST.get("batch_id"))
        finish_machine(machine=machine, batch=batch, user=request.user, note=note)
        finish_stage(batch, user=request.user, note=note)
    messages.success(request, "Apparatdagi ish tugatildi.")
    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def machine_broken(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    work_type = request.POST.get("work_type", "batch")
    reason = request.POST.get("reason", "").strip()
    note = request.POST.get("note", "").strip()
    if work_type == "order":
        order = get_object_or_404(Order, pk=request.POST.get("order_id"))
        report_machine_breakdown(machine=machine, order=order, user=request.user, reason=reason, note=note)
    else:
        batch = get_object_or_404(Batch, pk=request.POST.get("batch_id"))
        report_machine_breakdown(machine=machine, batch=batch, user=request.user, reason=reason, note=note)
    messages.error(request, "Apparat buzildi.")
    return redirect("machine_detail", machine_id=machine.pk)


@login_required
def mechanic_dashboard(request):
    breakdowns = MachineBreakdown.objects.select_related("machine", "batch", "batch__order", "order").all()
    return render(request, "production/mechanic_dashboard.html", {"breakdowns": breakdowns})


@login_required
def mechanic_accept(request, breakdown_id):
    breakdown = get_object_or_404(MachineBreakdown, pk=breakdown_id)
    accept_breakdown(breakdown, user=request.user, note=request.POST.get("note", "").strip())
    messages.success(request, "Mexanik qabul qildi.")
    return redirect("mechanic_dashboard")


@login_required
def mechanic_fix(request, breakdown_id):
    breakdown = get_object_or_404(MachineBreakdown, pk=breakdown_id)
    fix_breakdown(breakdown, user=request.user, note=request.POST.get("note", "").strip())
    messages.success(request, "Apparat tuzatildi.")
    return redirect("mechanic_dashboard")
