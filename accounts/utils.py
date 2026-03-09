from django.contrib import messages
from django.shortcuts import redirect


WORKER_GROUPS = {
    "RANG_TAYYORLOVCHI",
    "QUYUVCHI",
    "APPARATCHI",
    "PALIROFKACHI",
    "SARTIROVKACHI",
    "OMBORCHI",
    "JONATUVCHI",
    "MASTER",
}


def is_worker(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return False

    group_names = set(user.groups.values_list("name", flat=True))
    return bool(group_names.intersection(WORKER_GROUPS))


def redirect_worker_only(request):
    """
    Agar worker admin bo'limlarga kirsa, worker panelga qaytaradi.
    """
    if is_worker(request.user):
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo‘q.")
        return redirect("worker_dashboard")
    return None