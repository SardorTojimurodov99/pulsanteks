from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Batch, Stage, Machine, Order, Color, Finish


# ===== RUXSATLAR =====
def is_worker_or_staff(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or user.groups.filter(name="worker").exists()
    )


def in_group(user, group_name: str) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_staff or user.is_superuser or user.groups.filter(name=group_name).exists()


def require_dept(group_name: str, dept_label: str):
    """
    dept bo‘limga kirish: staff/superuser yoki tegishli group bo‘lsa.
    """
    def decorator(view_func):
        @login_required
        @user_passes_test(is_worker_or_staff)
        def _wrapped(request, *args, **kwargs):
            if in_group(request.user, group_name):
                return view_func(request, *args, **kwargs)
            return render(request, "worker/forbidden.html", {"dept": dept_label})
        return _wrapped
    return decorator


# ===== DASHBOARD (hamma worker ko‘radi) =====
@login_required
@user_passes_test(is_worker_or_staff)
def dashboard(request):
    q = request.GET.get("q", "").strip()
    stage = request.GET.get("stage", "").strip()
    machine = request.GET.get("machine", "").strip()
    paused = request.GET.get("paused", "").strip()
    done = request.GET.get("done", "").strip()

    batches = (
        Batch.objects
        .select_related("order", "order__color", "machine")
        .order_by("-updated_at")
    )

    if q:
        batches = batches.filter(
            Q(order__customer_name__icontains=q) |
            Q(order__id__icontains=q) |
            Q(order__color__name__icontains=q) |
            Q(order__size_mm__icontains=q) |
            Q(order__laser_text__icontains=q) |
            Q(title__icontains=q)
        )

    if stage:
        batches = batches.filter(stage=stage)

    if machine:
        batches = batches.filter(machine__code=machine)

    if paused.lower() in ("1", "true", "yes", "on"):
        batches = batches.filter(is_paused=True)

    if done.lower() in ("1", "true", "yes", "on"):
        batches = batches.filter(is_done=True)

    ctx = {
        "title": "Batchlar (umumiy)",
        "batches": batches[:300],
        "q": q,
        "stage": stage,
        "machine": machine,
        "paused": paused,
        "done": done,
        "stages": Stage.choices,
        "machines": Machine.objects.order_by("code"),
    }
    return render(request, "worker/dashboard.html", ctx)


# ===== BATCH =====
@login_required
@user_passes_test(is_worker_or_staff)
def batch_detail(request, pk: int):
    batch = get_object_or_404(
        Batch.objects.select_related("order", "order__color", "machine"),
        pk=pk,
    )
    return render(request, "worker/batch_detail.html", {"batch": batch})


@login_required
@user_passes_test(is_worker_or_staff)
def batch_update(request, pk: int):
    batch = get_object_or_404(
        Batch.objects.select_related("order", "order__color", "machine"),
        pk=pk,
    )

    if request.method == "POST":
        kg_done = (request.POST.get("kg_done") or "0").strip()
        list_done = (request.POST.get("list_done") or "0").strip()
        machine_code = (request.POST.get("machine_code") or "").strip()

        try:
            batch.kg_done = Decimal(kg_done)
        except Exception:
            messages.error(request, "kg noto‘g‘ri kiritildi.")
            return redirect("worker:batch_detail", pk=batch.pk)

        try:
            batch.list_done = int(list_done)
        except Exception:
            messages.error(request, "list noto‘g‘ri kiritildi.")
            return redirect("worker:batch_detail", pk=batch.pk)

        if machine_code:
            batch.machine = Machine.objects.filter(code=machine_code).first()
        else:
            batch.machine = None

        batch.save()
        messages.success(request, "Batch yangilandi.")
        return redirect("worker:batch_detail", pk=batch.pk)

    return render(
        request,
        "worker/batch_update.html",
        {"batch": batch, "machines": Machine.objects.order_by("code")},
    )


@login_required
@user_passes_test(is_worker_or_staff)
def batch_pause(request, pk: int):
    batch = get_object_or_404(Batch, pk=pk)
    batch.is_paused = True
    batch.save(update_fields=["is_paused", "updated_at"])
    messages.warning(request, "Batch pauzaga qo‘yildi.")
    return redirect("worker:dashboard")


@login_required
@user_passes_test(is_worker_or_staff)
def batch_done(request, pk: int):
    batch = get_object_or_404(Batch, pk=pk)
    batch.is_done = True
    batch.is_paused = False
    batch.save(update_fields=["is_done", "is_paused", "updated_at"])
    messages.success(request, "Batch tugadi deb belgilandi.")
    return redirect("worker:dashboard")


# ===== ZAKAZ =====
@require_dept("dept_zakaz", "Zakaz")
def zakaz_list(request):
    q = request.GET.get("q", "").strip()

    orders = (
        Order.objects
        .select_related("color")
        .order_by("-id")
    )

    if q:
        orders = orders.filter(
            Q(id__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(color__name__icontains=q) |
            Q(size_mm__icontains=q) |
            Q(laser_text__icontains=q)
        )

    return render(request, "worker/zakaz_list.html", {"orders": orders[:500], "q": q})


@require_dept("dept_zakaz", "Zakaz")
def zakaz_add(request):
    colors = Color.objects.order_by("name")

    if request.method == "POST":
        customer_name = (request.POST.get("customer_name") or "").strip()
        size_mm = (request.POST.get("size_mm") or "").strip()
        color_id = (request.POST.get("color_id") or "").strip()
        kg_plan = (request.POST.get("kg_plan") or "0").strip()
        list_plan = (request.POST.get("list_plan") or "0").strip()
        finish = (request.POST.get("finish") or Finish.YALTIROQ).strip()

        laser = (request.POST.get("laser") or "").strip() in ("1", "true", "on", "yes")
        laser_text = (request.POST.get("laser_text") or "").strip()

        if not customer_name or not size_mm or not color_id:
            messages.error(request, "Majburiy maydonlar to‘ldirilmadi.")
            return redirect("worker:zakaz_add")

        try:
            size_mm_int = int(size_mm)
        except Exception:
            messages.error(request, "O‘lcham noto‘g‘ri.")
            return redirect("worker:zakaz_add")

        try:
            kg_plan_dec = Decimal(kg_plan)
        except Exception:
            messages.error(request, "Kg noto‘g‘ri.")
            return redirect("worker:zakaz_add")

        try:
            list_plan_int = int(list_plan)
        except Exception:
            list_plan_int = 0

        color = get_object_or_404(Color, pk=color_id)

        if laser is False:
            laser_text = ""

        order = Order.objects.create(
            customer_name=customer_name,
            size_mm=size_mm_int,
            color=color,
            kg_plan=kg_plan_dec,
            list_plan=list_plan_int,
            finish=finish,
            laser=laser,
            laser_text=laser_text,
            stage=Stage.QABUL,
        )

        # yangi zakaz uchun 1 ta default batch ochib qo‘yamiz
        Batch.objects.create(
            order=order,
            title="Batch 1",
            kg_plan=kg_plan_dec,
            list_plan=list_plan_int,
            stage=Stage.QABUL,
        )

        messages.success(request, f"Zakaz yaratildi: #{order.id}")
        return redirect("worker:zakaz_list")

    return render(request, "worker/zakaz_add.html", {"colors": colors})


# ===== DEPT sahifalar (hozircha filter + ishlash uchun) =====
def _dept_page(request, dept_label: str, stage_value: str):
    # bosqichga tegishli batchlarni ko‘rsatadi
    q = request.GET.get("q", "").strip()
    batches = (
        Batch.objects
        .select_related("order", "order__color", "machine")
        .filter(stage=stage_value)
        .order_by("-updated_at")
    )
    if q:
        batches = batches.filter(
            Q(order__customer_name__icontains=q) |
            Q(order__color__name__icontains=q) |
            Q(order__id__icontains=q) |
            Q(title__icontains=q)
        )

    return render(request, "worker/dashboard.html", {
        "title": f"Bo‘lim: {dept_label}",
        "batches": batches[:300],
        "q": q,
        "stage": stage_value,
        "machine": "",
        "paused": "",
        "done": "",
        "stages": Stage.choices,
        "machines": Machine.objects.order_by("code"),
    })


@require_dept("dept_rang", "Rang")
def dept_rang(request): return _dept_page(request, "Rang", Stage.RANG)

@require_dept("dept_quyish", "Quyish")
def dept_quyish(request): return _dept_page(request, "Quyish", Stage.QUYISH)

@require_dept("dept_aparat", "Aparat")
def dept_aparat(request): return _dept_page(request, "Aparat", Stage.APARAT)

@require_dept("dept_yuvish", "Yuvish")
def dept_yuvish(request): return _dept_page(request, "Yuvish", Stage.YUVISH)

@require_dept("dept_mativiy", "Mativiy")
def dept_mativiy(request): return _dept_page(request, "Mativiy", Stage.MATIVIY)

@require_dept("dept_sartarofka", "Sartarofka")
def dept_sartarofka(request): return _dept_page(request, "Sartarofka", Stage.SARTAROFKA)

@require_dept("dept_upakovka", "Upakovka")
def dept_upakovka(request): return _dept_page(request, "Upakovka", Stage.UPAKOVKA)

@require_dept("dept_ombor", "Ombor")
def dept_ombor(request): return _dept_page(request, "Ombor", Stage.OMBOR)

@require_dept("dept_jonatish", "Jo‘natish")
def dept_jonatish(request): return _dept_page(request, "Jo‘natish", Stage.JONATISH)