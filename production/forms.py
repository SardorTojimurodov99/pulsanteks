from django import forms
from .models import Batch, Stage
from orders.models import Order, OrderItem


class BatchForm(forms.ModelForm):
    order = forms.ModelChoiceField(
        queryset=Order.objects.filter(status="RELEASED").order_by("-id"),
        label="Zakas",
    )
    order_item = forms.ModelChoiceField(
        queryset=OrderItem.objects.select_related("order").all().order_by("order_id", "id"),
        label="Zakas qatori",
    )

    class Meta:
        model = Batch
        fields = ["order", "order_item", "batch_no", "quantity", "stage", "status"]
        widgets = {
            "stage": forms.Select(),
            "status": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stage"].initial = Stage.RANG_TAYYORLASH
        self.fields["status"].initial = "NEW"

    def clean(self):
        cleaned = super().clean()
        order = cleaned.get("order")
        order_item = cleaned.get("order_item")
        if order and order_item and order_item.order_id != order.id:
            raise forms.ValidationError("Tanlangan zakas qatori tanlangan zakasga tegishli emas.")
        return cleaned
