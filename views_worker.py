from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import Batch, Stage, MachineStatus
from .forms import BatchAssignMachineForm
from .services import mark_batch_done_and_advance

# Group -> Stage mapping (ishchini qaysi bo‘limga qo‘ysangiz shu stage chiqadi)
GROUP_STAGE = {
    "rang": Stage.RANG,
    "quyish": Stage.QUYISH,
    "aparat": Stage.APARAT,
    "yuvish": Stage.YUVISH,
    "upakovka": Stage.UPAKOVKA,
    "ombor": Stage.OMBOR,
    "jonatish": Stage.JONATISH,
}

def _user_stage(user):
    # superuser hammasini ko‘rsin
    if user.is_superuser:
        return None
    user_groups = set(user.groups.values_list("name", flat=True))
    for g, st in GROUP_STAGE.items():
        if g in user_groups:
            return st
    return None  # group topilmasa (xohlasangiz forbiddenga o‘tkazamiz)

@require_http_methods(["GET", "POST"])
def worker_login(request):
    if request.user.is_authenticated:
        return redirect("worker_dashboard")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("worker_dashboard")
        error = "Login yoki parol noto‘g‘ri"

    return render(request, "worker/login.html", {"error": error})

@login_required
def worker_logout(request):
    logout(request)
    return redirect("worker_login")

@login_required
def worker_dashboard(request):
    st = _user_stage(request.user)

    qs = Batch.objects.select_related("order", "order__color", "machine").order_by("-id")

    # Superuser: hammasi
    if st:
        qs = qs.filter(stage=st)

    # faqat tugamagan ishlar
    qs = qs.filter(is_done=False)

    return render(request, "worker/dashboard.html", {"batches": qs, "stage": st})

@login_required
def batch_detail(request, batch_id: int):
    batch = get_object_or_404(Batch.objects.select_related("order", "order__color", "machine"), id=batch_id)

    st = _user_stage(request.user)
    if st and batch.stage != st:
        return HttpResponseForbidden("Siz bu bo‘limga kira olmaysiz")

    form = BatchAssignMachineForm(instance=batch)

    return render(request, "worker/batch_detail.html", {"batch": batch, "form": form})

@login_required
@require_http_methods(["POST"])
def assign_machine(request, batch_id: int):
    batch = get_object_or_404(Batch.objects.select_related("machine"), id=batch_id)

    st = _user_stage(request.user)
    if st and batch.stage != st:
        return HttpResponseForbidden("Siz bu bo‘limga kira olmaysiz")

    # faqat APARAT bosqichida mashina tanlanadi
    if batch.stage != Stage.APARAT:
        return HttpResponseForbidden("Mashina faqat APARAT bosqichida biriktiriladi")

    form = BatchAssignMachineForm(request.POST, instance=batch)
    if form.is_valid():
        batch = form.save(commit=False)

        if batch.machine_id:
            m = batch.machine
            # band qilish
            m.status = MachineStatus.BUSY
            m.current_batch = batch
            m.busy_since = m.busy_since or timezone.now()
            m.save(update_fields=["status", "current_batch", "busy_since"])

        batch.save(update_fields=["machine"])

    return redirect("batch_detail", batch_id=batch_id)

@login_required
@require_http_methods(["POST"])
def done_and_next(request, batch_id: int):
    batch = get_object_or_404(Batch.objects.select_related("order", "machine"), id=batch_id)

    st = _user_stage(request.user)
    if st and batch.stage != st:
        return HttpResponseForbidden("Siz bu bo‘limga kira olmaysiz")

    note = (request.POST.get("note") or "").strip()

    # APARAT stage da mashina tanlanmagan bo‘lsa — o‘tkazmaymiz
    if batch.stage == Stage.APARAT and not batch.machine_id:
        return HttpResponseForbidden("APARAT bosqichida mashina tanlanishi shart!")

    mark_batch_done_and_advance(batch, note=note)
    return redirect("worker_dashboard")