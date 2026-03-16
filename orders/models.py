from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


WORKFLOW_STAGE_CHOICES = [
    ("RANG_TAYYORLASH", "Rang tayyorlash"),
    ("QUYISH", "Quyish"),
    ("APPARAT", "Apparat"),
    ("PALIROFKA", "Palirofka"),
    ("SARTIROVKA", "Sartirovka"),
    ("OMBOR", "Ombor"),
    ("JONATISH", "Jo'natish"),
]


class OrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "Qoralama"
    RELEASED = "RELEASED", "Ish jarayonida"
    DONE = "DONE", "Tugadi"


class SurfaceType(models.TextChoices):
    MATTE = "MATTE", "Mat"
    GLOSSY = "GLOSSY", "Yalt"


class LaserType(models.TextChoices):
    LASER = "LASER", "Lazer"
    NO_LASER = "NO_LASER", "Lazersiz"


class MaterialType(models.TextChoices):
    SADAF = "SADAF", "Sadaf"
    POLEGAL = "POLEGAL", "Polegal"


class Order(models.Model):
    order_date = models.DateField(verbose_name="Sana")
    accepted_at = models.DateField(verbose_name="Qabul qilingan sana")
    order_no = models.CharField(max_length=30, unique=True, verbose_name="Zakaz raqami")
    customer_name = models.CharField(max_length=255, verbose_name="Firma nomi")
    due_at = models.DateTimeField(verbose_name="Topshirish vaqti")
    note = models.TextField(blank=True, verbose_name="Izoh")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
        verbose_name="Holati",
    )
    current_stage = models.CharField(
        max_length=30,
        choices=WORKFLOW_STAGE_CHOICES,
        default="RANG_TAYYORLASH",
        verbose_name="Joriy bo'lim",
    )
    use_order_flow = models.BooleanField(
        default=True,
        verbose_name="Zakaz o'zi worker oqimida ko'rinsin",
    )
    released_at = models.DateTimeField(null=True, blank=True, verbose_name="Jarayonga o'tgan vaqt")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.order_no} - {self.customer_name}"

    @property
    def item(self):
        return self.items.order_by("id").first()

    @property
    def total_smala_kg(self):
        item = self.item
        if not item:
            return Decimal("0")
        return (item.smala_kg or Decimal("0")) * item.sheet_count

    @property
    def total_button_count(self):
        item = self.item
        return item.button_count if item else 0

    def processed_list_count_for_stage(self, stage=None):
        source_stage = stage or self.current_stage
        return sum(
            self.batches.filter(unit_type="LIST", is_repeat=False, source_stage=source_stage).values_list("quantity", flat=True)
        )

    @property
    def processed_list_count(self):
        return self.processed_list_count_for_stage(self.current_stage)

    def remaining_list_count_for_stage(self, stage=None):
        item = self.item
        if not item:
            return 0
        return max(item.sheet_count - self.processed_list_count_for_stage(stage), 0)

    @property
    def remaining_list_count(self):
        return self.remaining_list_count_for_stage(self.current_stage)

    def processed_button_count_for_stage(self, stage=None):
        source_stage = stage or self.current_stage
        return sum(
            self.batches.filter(unit_type="BUTTON", is_repeat=False, source_stage=source_stage).values_list("quantity", flat=True)
        )

    @property
    def processed_button_count(self):
        return self.processed_button_count_for_stage(self.current_stage)

    def remaining_button_count_for_stage(self, stage=None):
        item = self.item
        if not item:
            return 0
        return max(item.button_count - self.processed_button_count_for_stage(stage), 0)

    @property
    def remaining_button_count(self):
        return self.remaining_button_count_for_stage(self.current_stage)

    def remaining_quantity_for_current_stage(self):
        if self.current_stage == "SARTIROVKA":
            return self.remaining_button_count_for_stage(self.current_stage)
        return self.remaining_list_count_for_stage(self.current_stage)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Zakaz",
    )
    size = models.CharField(max_length=50, verbose_name="Razmeri")
    primary_color = models.CharField(max_length=100, verbose_name="Asosiy rangi")
    secondary_color = models.CharField(max_length=100, blank=True, verbose_name="Qavat rangi")
    pantone = models.CharField(max_length=50, blank=True, verbose_name="Pantone")
    material_type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        default=MaterialType.SADAF,
        verbose_name="Sadaf / Polegal",
    )
    is_coated = models.BooleanField(default=False, verbose_name="Qavatli")
    coating_count = models.PositiveIntegerField(default=0, verbose_name="Qavat soni")
    coating_note = models.CharField(max_length=255, blank=True, verbose_name="Qavat izohi")
    hole_count = models.PositiveIntegerField(default=0, verbose_name="Teshigi soni")
    surface = models.CharField(
        max_length=20,
        choices=SurfaceType.choices,
        verbose_name="Mat / Yalt",
    )
    laser = models.CharField(
        max_length=20,
        choices=LaserType.choices,
        default=LaserType.NO_LASER,
        verbose_name="Lazer / Lazersiz",
    )
    laser_note = models.CharField(max_length=255, blank=True, verbose_name="Lazer yozuvi")
    sheet_count = models.PositiveIntegerField(verbose_name="List soni")
    button_count = models.PositiveIntegerField(verbose_name="Umumiy tugma soni")
    smala_kg = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Smala kg")
    thickness = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Qalinligi")
    note = models.TextField(blank=True, verbose_name="Izoh")

    class Meta:
        ordering = ["id"]
        verbose_name = "Zakaz tarkibi"
        verbose_name_plural = "Zakaz tarkiblari"

    def __str__(self):
        return f"{self.order.order_no} / {self.size} / {self.primary_color}"

    def clean(self):
        if self.sheet_count <= 0:
            raise ValidationError("List soni 0 dan katta bo'lishi kerak.")
        if self.button_count <= 0:
            raise ValidationError("Umumiy tugma soni 0 dan katta bo'lishi kerak.")
        if self.smala_kg <= 0:
            raise ValidationError("Smala kg 0 dan katta bo'lishi kerak.")
        if self.thickness <= 0:
            raise ValidationError("Qalinligi 0 dan katta bo'lishi kerak.")
        if self.is_coated and self.coating_count <= 0:
            raise ValidationError("Qavatli bo'lsa qavat soni kiritilishi kerak.")
        if self.laser == LaserType.LASER and not self.laser_note.strip():
            raise ValidationError("Lazer tanlansa, lazer yozuvi kiritilishi kerak.")
