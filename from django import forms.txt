from django import forms
from .models import Batch, Machine

class BatchAssignMachineForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["machine"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # faqat bo‘sh (IDLE) mashinalar chiqsin
        self.fields["machine"].queryset = Machine.objects.filter(status="IDLE").order_by("code")
        self.fields["machine"].required = False