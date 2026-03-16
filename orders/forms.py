from django import forms

from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "order_date",
            "accepted_at",
            "order_no",
            "customer_name",
            "due_at",
            "note",
        ]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
            "accepted_at": forms.DateInput(attrs={"type": "date"}),
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = [
            "size",
            "primary_color",
            "secondary_color",
            "pantone",
            "material_type",
            "is_coated",
            "coating_count",
            "coating_note",
            "hole_count",
            "surface",
            "laser",
            "laser_note",
            "sheet_count",
            "button_count",
            "smala_kg",
            "thickness",
            "note",
        ]
        widgets = {
            "coating_note": forms.TextInput(),
            "laser_note": forms.TextInput(),
            "note": forms.Textarea(attrs={"rows": 2}),
        }
