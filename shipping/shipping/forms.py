from django import forms
from django.forms import inlineformset_factory
from .models import Shipment, ShipmentItem


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ["shipment_no", "customer_name", "shipped_at", "note"]
        widgets = {
            "shipped_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ShipmentItemForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ["warehouse_lot", "quantity"]


ShipmentItemFormSet = inlineformset_factory(
    Shipment,
    ShipmentItem,
    form=ShipmentItemForm,
    extra=1,
    can_delete=True,
)