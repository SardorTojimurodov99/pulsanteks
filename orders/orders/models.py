from django.core.exceptions import ValidationError
from django.db import models


class OrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "Saqlangan"
    RELEASED = "RELEASED", "Ishlab chiqarishga o'tkazilgan"


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
        default=OrderStatus.DRAFT,
        verbose_name="Holati",
    )
    released_at = models.DateTimeField(null=True, blank=True, verbose_name="Ishlab chiqarishga o'tkazilgan vaqt")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_no} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Zakas",
    )

    size = models.CharField(max_length=50, verbose_name="Razmer")
    color = models.CharField(max_length=100, verbose_name="Rangi")

    is_coated = models.BooleanField(default=False, verbose_name="Qavatli")
    coating_note = models.CharField(max_length=255, blank=True, verbose_name="Qavat izohi")

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
    laser_note = models.CharField(max_length=255, blank=True, verbose_name="Lazer yozuvi")

    sheet_count = models.PositiveIntegerField(verbose_name="List soni")
    button_count = models.PositiveIntegerField(default=0, verbose_name="Tugma soni")

    smala_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Smala kg"
    )

    note = models.TextField(blank=True, verbose_name="Izoh")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.order.order_no} / {self.size} / {self.color}"

    def clean(self):
        if self.sheet_count <= 0:
            raise ValidationError("List soni 0 dan katta bo'lishi kerak.")
        if self.smala_kg <= 0:
            raise ValidationError("Smala kg 0 dan katta bo'lishi kerak.")
        if self.is_coated and not self.coating_note.strip():
            raise ValidationError("Qavatli bo'lsa, qavat izohi kiritilishi kerak.")
        if self.laser == LaserType.LASER and not self.laser_note.strip():
            raise ValidationError("Lazerli bo'lsa, lazer yozuvi kiritilishi kerak.")