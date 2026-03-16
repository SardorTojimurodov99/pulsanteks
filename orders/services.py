from django.utils import timezone

from .models import Order, OrderStatus


STAGE_SEQUENCE = [
    "RANG_TAYYORLASH",
    "QUYISH",
    "APPARAT",
    "PALIROFKA",
    "SARTIROVKA",
    "OMBOR",
    "JONATISH",
]


def generate_order_no():
    last = Order.objects.order_by("-id").first()
    if not last:
        return "ZK-0001"

    try:
        num = int(last.order_no.split("-")[-1])
    except Exception:
        num = last.id

    return f"ZK-{num + 1:04d}"


def next_stage(stage):
    try:
        idx = STAGE_SEQUENCE.index(stage)
    except ValueError:
        return None
    if idx + 1 < len(STAGE_SEQUENCE):
        return STAGE_SEQUENCE[idx + 1]
    return None


def release_order_to_production(order):
    if order.status == OrderStatus.RELEASED:
        return order

    order.status = OrderStatus.RELEASED
    order.released_at = timezone.now()
    order.current_stage = "RANG_TAYYORLASH"
    order.use_order_flow = True
    order.save(update_fields=["status", "released_at", "current_stage", "use_order_flow"])
    return order


def refresh_order_done_state(order):
    if order.status == OrderStatus.DRAFT:
        return order

    if order.batches.exists():
        all_shipped = not order.batches.exclude(status="SHIPPED").exists()
        if all_shipped:
            order.status = OrderStatus.DONE
            order.use_order_flow = False
            order.current_stage = "JONATISH"
            order.save(update_fields=["status", "use_order_flow", "current_stage"])
    return order
