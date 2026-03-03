from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Batch

@login_required
def worker_dashboard(request):
    # Ishchi ko‘radigan ro‘yxat: oxirgi batchlar
    batches = (
        Batch.objects
        .select_related("order", "order__color", "machine")
        .order_by("-id")[:200]
    )

    return render(request, "worker/dashboard.html", {"batches": batches})