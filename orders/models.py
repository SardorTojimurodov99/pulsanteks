from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class OrderStatus(models.TextChoices):
    NEW = "NEW", "Yangi"
    CONFIRMED = "CONFIRMED", "Tasdiqlangan"
    IN_PROGRESS = "IN_PROGRESS", "Ishlab chiqarishda"
    PARTIAL_READY = "PARTIAL_READY", "Qisman tayyor"
    READY = "READY", "Tayyor"
    SHIPPED = "SHIPPED", "Jo'natilgan"
    CANCELLED = "CANCELLED", "Bekor qilingan"


class CoatingType(models.TextChoices):
    SADAF = "SADAF", "Sadaf"
    POLEGAL = "POLEGAL", "Polegal"
    NONE = "NONE", "Qavatsiz"


class SurfaceType(models.TextChoices):
    MATTE = "MATTE", "Mateviy"
    GLOSSY = "GLOSSY", "Yaltiroq"


class LaserType(models.TextChoices):
    LASER = "LASER", "Lazerli"
    NO_LASER = "NO_LASER", "Lazersiz"


class Order(models.Model):
    order_no = models.CharField(max_length=30, unique=True, verbose_name="Zakas raqami")
    accepted_at = models.DateField(verbose_name="Qabul qilingan sana")
    customer_name = models.CharField(max_length=255, verbose_name="Firma nomi")
    due_at = models.DateTimeField(verbose_name="Topshirish vaqti")
    note = models.TextField(blank=True, verbose_name="Izoh")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        verbose_name="Holati",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-accepted_at", "-id"]
        verbose_name = "Zakas"
        verbose_name_plural = "Zakazlar"

    def __str__(self):
        return f"{self.order_no} - {self.customer_name}"

    def clean(self):
        if self.due_at.date() < self.accepted_at:
            raise ValidationError("Topshirish vaqti qabul qilingan sanadan oldin bo'lishi mumkin emas.")

    @property
    def total_sheets(self):
        return sum(item.sheet_count for item in self.items.all())

    @property
    def total_buttons(self):
        return sum(item.button_count for item in self.items.all())

    @property
    def total_smala_kg(self):
        return sum((item.smala_kg for item in self.items.all()), Decimal("0"))

    @property
    def is_overdue(self):
        return self.status not in [
            OrderStatus.READY,
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
        ] and timezone.now() > self.due_at


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Zakas",
    )
    size = models.CharField(max_length=50, verbose_name="Razmer")
    color = models.CharField(max_length=100, verbose_name="Rangi")
    coating = models.CharField(
        max_length=20,
        choices=CoatingType.choices,
        default=CoatingType.NONE,
        verbose_name="Sadaf yoki polegal",
    )
    techik_count = models.PositiveIntegerField(default=0, verbose_name="Techik soni")
    surface = models.CharField(
        max_length=20,
        choices=SurfaceType.choices,
        verbose_name="Mateviy yoki yaltiroq",
    )
    laser = models.CharField(
        max_length=20,
        choices=LaserType.choices,
        default=LaserType.NO_LASER,
        verbose_name="Lazer yoki lazersiz",
    )
    sheet_count = models.PositiveIntegerField(verbose_name="List soni")
    button_count = models.PositiveIntegerField(default=0, verbose_name="Tugma soni")
    kg_per_sheet = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name="1 listga ketadigan kg",
    )
    smala_kg = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        editable=False,
        verbose_name="Smala kg",
    )
    note = models.TextField(blank=True, verbose_name="Izoh")

    class Meta:
        ordering = ["id"]
        verbose_name = "Zakas qatori"
        verbose_name_plural = "Zakas qatorlari"

    def __str__(self):
        return f"{self.order.order_no} / {self.size} / {self.color}"

    def clean(self):
        if self.sheet_count <= 0:
            raise ValidationError("List soni 0 dan katta bo'lishi kerak.")
        if self.kg_per_sheet <= 0:
            raise ValidationError("1 listga ketadigan kg 0 dan katta bo'lishi kerak.")

    def save(self, *args, **kwargs):
        self.smala_kg = (Decimal(self.sheet_count) * self.kg_per_sheet).quantize(Decimal("0.0001"))
        super().save(*args, **kwargs)