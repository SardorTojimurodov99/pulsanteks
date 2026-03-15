from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ShipmentForm, ShipmentItemFormSet
from .models import Shipment
from .services import apply_shipment, generate_shipment_no
from accounts.utils import redirect_worker_only


def shipment_list(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    shipments = Shipment.objects.prefetch_related("items").all()
    return render(request, "shipping/shipment_list.html", {"shipments": shipments})


def shipment_detail(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    shipment = get_object_or_404(Shipment.objects.prefetch_related("items"), pk=pk)
    return render(request, "shipping/shipment_detail.html", {"shipment": shipment})


@transaction.atomic
def shipment_create(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    if request.method == "POST":
        form = ShipmentForm(request.POST)
        formset = ShipmentItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            shipment = form.save(commit=False)
            if not shipment.shipment_no:
                shipment.shipment_no = generate_shipment_no()
            shipment.save()

            formset.instance = shipment
            formset.save()
            apply_shipment(shipment)

            messages.success(request, "Jo'natma yaratildi.")
            return redirect("shipment_detail", pk=shipment.pk)
    else:
        form = ShipmentForm(initial={
            "shipment_no": generate_shipment_no(),
            "shipped_at": timezone.now().strftime("%Y-%m-%dT%H:%M"),
        })
        formset = ShipmentItemFormSet()

    return render(request, "shipping/shipment_form.html", {
        "form": form,
        "formset": formset,
        "title": "Yangi jo'natma",
    })