from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderForm, OrderItemFormSet
from .models import Order
from .services import generate_order_no
from production.services import create_batches_for_order


def order_list(request):
    qs = Order.objects.prefetch_related("items").all()
    q = request.GET.get("q", "").strip()

    if q:
        qs = qs.filter(Q(order_no__icontains=q) | Q(customer_name__icontains=q))

    return render(request, "orders/order_list.html", {
        "orders": qs,
        "q": q,
    })


def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    return render(request, "orders/order_detail.html", {"order": order})


@transaction.atomic
def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            if not order.order_no:
                order.order_no = generate_order_no()
            order.save()

            formset.instance = order
            items = formset.save()

            if not items:
                messages.error(request, "Kamida 1 ta zakas qatori bo'lishi kerak.")
                return render(request, "orders/order_form.html", {
                    "form": form,
                    "formset": formset,
                    "title": "Yangi zakas",
                })

            create_batches_for_order(order)
            messages.success(request, "Zakas yaratildi.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderForm(initial={"order_no": generate_order_no()})
        formset = OrderItemFormSet()

    return render(request, "orders/order_form.html", {
        "form": form,
        "formset": formset,
        "title": "Yangi zakas",
    })


@transaction.atomic
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            order.batches.all().delete()
            create_batches_for_order(order)

            messages.success(request, "Zakas yangilandi.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)

    return render(request, "orders/order_form.html", {
        "form": form,
        "formset": formset,
        "title": "Zakasni tahrirlash",
    })


@transaction.atomic
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        order.delete()
        messages.success(request, "Zakas o‘chirildi.")
        return redirect("order_list")

    return render(request, "orders/order_confirm_delete.html", {"order": order})