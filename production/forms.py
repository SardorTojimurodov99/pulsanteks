from django import forms

from .models import Stage


class BatchCreateForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Miqdor")
    is_repeat = forms.BooleanField(required=False, label="Takror batch")
    scrap_quantity = forms.IntegerField(min_value=0, required=False, initial=0, label="Brak tugma soni")
    inspection_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Rang nazorati")
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Izoh")

    def __init__(self, *args, order=None, stage=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order
        self.stage = stage
        if stage == Stage.SARTIROVKA:
            self.fields["quantity"].label = "Yaroqli tugma soni"
            self.fields["scrap_quantity"].required = True
            self.fields["inspection_note"].required = True
        else:
            self.fields["scrap_quantity"].widget = forms.HiddenInput()
            self.fields["inspection_note"].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get("quantity") or 0
        scrap = cleaned.get("scrap_quantity") or 0
        is_repeat = cleaned.get("is_repeat")

        if self.stage == Stage.SARTIROVKA:
            if quantity <= 0:
                raise forms.ValidationError("Yaroqli tugma soni 0 dan katta bo'lishi kerak.")
            if self.order and not is_repeat:
                if quantity + scrap > self.order.remaining_button_count_for_stage(self.stage):
                    raise forms.ValidationError("Qolgan tugma sonidan ko'p batch yaratib bo'lmaydi.")
        else:
            if self.order and not is_repeat:
                if quantity > self.order.remaining_list_count_for_stage(self.stage):
                    raise forms.ValidationError("Qolgan list sonidan ko'p batch yaratib bo'lmaydi.")
        return cleaned
