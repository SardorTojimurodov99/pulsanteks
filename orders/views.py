from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import redirect_worker_only
from .forms import OrderForm, OrderItemForm
from .models import Order, OrderItem, OrderStatus
from .services import generate_order_no, release_order_to_production, refresh_order_done_state



def order_list(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    q = request.GET.get("q", "").strip()
    orders = Order.objects.prefetch_related("items", "batches").all()

    if q:
        orders = orders.filter(Q(order_no__icontains=q) | Q(customer_name__icontains=q))

    return render(request, "orders/order_list.html", {"orders": orders, "q": q})



def order_detail(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    order = get_object_or_404(Order.objects.prefetch_related("items", "batches", "batches__progresses"), pk=pk)
    refresh_order_done_state(order)
    return render(request, "orders/order_detail.html", {"order": order, "item": order.item})


@transaction.atomic
def order_create(request):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    if request.method == "POST":
        form = OrderForm(request.POST)
        item_form = OrderItemForm(request.POST)
        if form.is_valid() and item_form.is_valid():
            order = form.save(commit=False)
            if not order.order_no:
                order.order_no = generate_order_no()
            order.save()

            item = item_form.save(commit=False)
            item.order = order
            item.save()

            action = request.POST.get("action")
            if action == "save_release":
                release_order_to_production(order)
                messages.success(request, "Zakaz saqlandi va ishlab chiqarishga o'tkazildi.")
            else:
                messages.success(request, "Zakaz saqlandi.")

            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderForm(initial={"order_no": generate_order_no()})
        item_form = OrderItemForm()

    return render(request, "orders/order_form.html", {
        "form": form,
        "item_form": item_form,
        "title": "Zakaz yaratish",
    })


@transaction.atomic
def order_update(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    order = get_object_or_404(Order, pk=pk)
    item = order.item or OrderItem(order=order)

    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        item_form = OrderItemForm(request.POST, instance=item)
        if form.is_valid() and item_form.is_valid():
            form.save()
            item = item_form.save(commit=False)
            item.order = order
            item.save()
            messages.success(request, "Zakaz yangilandi.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderForm(instance=order)
        item_form = OrderItemForm(instance=item)

    return render(request, "orders/order_form.html", {
        "form": form,
        "item_form": item_form,
        "title": "Zakazni tahrirlash",
        "order": order,
    })


@transaction.atomic
def order_delete(request, pk):
    blocked = redirect_worker_only(request)
    if blocked:
        return blocked

    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        order.delete()
        messages.success(request, "Zakaz o'chirildi.")
        return redirect("order_list")
    return render(request, "orders/order_confirm_delete.html", {"order": order})
