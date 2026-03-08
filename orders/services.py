from django.db.models import Count
from orders.models import Order, OrderStatus
from production.models import BatchStatus


def generate_order_no():
    last = Order.objects.order_by("-id").first()
    if not last:
        return "ZK-0001"
    try:
        num = int(last.order_no.split("-")[-1])
    except Exception:
        num = last.id
    return f"ZK-{num + 1:04d}"


def recalc_order_status(order: Order):
    batches = order.batch_set.all() if hasattr(order, "batch_set") else None

    if batches is None:
        qs = order.items.all()
        if qs.exists():
            order.status = OrderStatus.CONFIRMED
        else:
            order.status = OrderStatus.NEW
        order.save(update_fields=["status"])
        return

    total = batches.count()
    if total == 0:
        order.status = OrderStatus.CONFIRMED if order.items.exists() else OrderStatus.NEW
    else:
        done = batches.filter(status=BatchStatus.DONE).count()
        in_progress = batches.filter(status=BatchStatus.IN_PROGRESS).count()
        warehouse_done = batches.filter(status=BatchStatus.WAREHOUSE).count()
        shipped = batches.filter(status=BatchStatus.SHIPPED).count()

        if shipped == total:
            order.status = OrderStatus.SHIPPED
        elif warehouse_done == total or done == total:
            order.status = OrderStatus.READY
        elif done > 0 or warehouse_done > 0:
            order.status = OrderStatus.PARTIAL_READY
        elif in_progress > 0:
            order.status = OrderStatus.IN_PROGRESS
        else:
            order.status = OrderStatus.CONFIRMED

    order.save(update_fields=["status"])