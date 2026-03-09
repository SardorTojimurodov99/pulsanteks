from django.shortcuts import render
from orders.models import Order
from production.models import Batch, BatchStatus
from warehouse.models import WarehouseLot
from shipping.models import Shipment


def dashboard_home(request):
    latest_orders = Order.objects.order_by("-id")[:10]
    latest_batches = Batch.objects.select_related("order").order_by("-id")[:10]

    context = {
        "total_orders": Order.objects.count(),
        "total_batches": Batch.objects.count(),
        "active_batches": Batch.objects.filter(status=BatchStatus.IN_PROGRESS).count(),
        "warehouse_lots": WarehouseLot.objects.count(),
        "shipments": Shipment.objects.count(),
        "latest_orders": latest_orders,
        "latest_batches": latest_batches,
    }
    return render(request, "dashboard/home.html", context)