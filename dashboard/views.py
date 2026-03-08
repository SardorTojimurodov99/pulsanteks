from django.shortcuts import render
from orders.models import Order
from production.models import Batch
from warehouse.models import WarehouseLot
from shipping.models import Shipment


def dashboard_home(request):
    context = {
        "total_orders": Order.objects.count(),
        "total_batches": Batch.objects.count(),
        "warehouse_lots": WarehouseLot.objects.count(),
        "shipments": Shipment.objects.count(),
        "latest_orders": Order.objects.order_by("-id")[:10],
    }
    return render(request, "dashboard/home.html", context)