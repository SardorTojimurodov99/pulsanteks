from .models import Order


def generate_order_no():
    last = Order.objects.order_by("-id").first()
    if not last:
        return "ZK-0001"

    try:
        num = int(last.order_no.split("-")[-1])
    except Exception:
        num = last.id

    return f"ZK-{num + 1:04d}"