from django.utils import timezone
from .models import Order, OrderStatus


def generate_order_no():
    last = Order.objects.order_by("-id").first()
    if not last:
        return "ZK-0001"

    try:
        num = int(last.order_no.split("-")[-1])
    except Exception:
        num = last.id

    return f"ZK-{num + 1:04d}"


def release_order_to_production(order):
    """
    Zakazni ishlab chiqarishga o'tkazadi.
    Batchlar BU YERDA avtomatik yaratilmaydi.
    Batchlarni ishchilar yoki admin qo'lda yaratadi.
    """
    if order.status == OrderStatus.RELEASED:
        return order

    order.status = OrderStatus.RELEASED
    order.released_at = timezone.now()
    order.save(update_fields=["status", "released_at"])
    return order
