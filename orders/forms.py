from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["order_no", "accepted_at", "customer_name", "due_at", "note"]
        widgets = {
            "accepted_at": forms.DateInput(attrs={"type": "date"}),
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = [
            "size",
            "color",
            "is_coated",
            "coating_note",
            "techik_count",
            "surface",
            "laser",
            "laser_note",
            "sheet_count",
            "button_count",
            "smala_kg",
            "note",
        ]


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
)