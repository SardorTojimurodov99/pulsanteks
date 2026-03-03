from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# =========================
# ENUMS
# =========================
class Stage(models.TextChoices):
    QABUL = "QABUL", _("Zakaz qabul")
    RANG = "RANG", _("Rang tayyor")
    QUYISH = "QUYISH", _("Quyish")
    APARAT = "APARAT", _("Aparat")
    YUVISH = "YUVISH", _("Yuvish")
    MATIVIY = "MATIVIY", _("Mativiy")
    SARTAROFKA = "SARTAROFKA", _("Sartarofka")
    UPAKOVKA = "UPAKOVKA", _("Upakovka")
    OMBOR = "OMBOR", _("Ombor")
    JONATISH = "JONATISH", _("Jo'natish")
    DONE = "DONE", _("Yakunlandi")


class Finish(models.TextChoices):
    YALTIROQ = "YALTIROQ", _("Yaltiroq")
    MATIVIY = "MATIVIY", _("Mativiy")


class MachineStatus(models.TextChoices):
    IDLE = "IDLE", _("Bo'sh")
    BUSY = "BUSY", _("Band")
    BROKEN = "BROKEN", _("Buzilgan")
    MAINT = "MAINT", _("Ta'mirda")


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", _("Ochiq")
    IN_PROGRESS = "IN_PROGRESS", _("Jarayonda")
    DONE = "DONE", _("Yopildi")


class Severity(models.TextChoices):
    LOW = "LOW", _("Past")
    MEDIUM = "MEDIUM", _("O'rtacha")
    HIGH = "HIGH", _("Yuqori")


# =========================
# KATALOG
# =========================
class Color(models.Model):
    name = models.CharField(_("Rang nomi"), max_length=120, unique=True)

    class Meta:
        verbose_name = _("Rang")
        verbose_name_plural = _("Ranglar")
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================
# ZAKAZ
# =========================
class Order(models.Model):
    customer_name = models.CharField(_("Zakaz beruvchi nomi"), max_length=200)
    size_mm = models.PositiveIntegerField(_("O'lcham (mm)"))
    color = models.ForeignKey(Color, on_delete=models.PROTECT, verbose_name=_("Rang"))

    kg_plan = models.DecimalField(_("Nechi kg quyish"), max_digits=10, decimal_places=2)
    list_plan = models.PositiveIntegerField(_("List soni"), default=0)

    finish = models.CharField(_("Finish"), max_length=20, choices=Finish.choices, default=Finish.YALTIROQ)

    laser = models.BooleanField(_("Lazer"), default=False)
    laser_text = models.CharField(_("Lazer matni"), max_length=255, blank=True, default="")

    stage = models.CharField(_("Bosqich"), max_length=20, choices=Stage.choices, default=Stage.QABUL)

    created_at = models.DateTimeField(_("Yaratilgan sana"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan sana"), auto_now=True)

    class Meta:
        verbose_name = _("Zakaz")
        verbose_name_plural = _("Zakazlar")
        ordering = ["-id"]

    def __str__(self):
        return f"Zakaz #{self.id} — {self.customer_name} ({self.size_mm}mm, {self.color})"

    def needs_matte(self) -> bool:
        return self.finish == Finish.MATIVIY

    def flow(self):
        base = [
            Stage.QABUL,
            Stage.RANG,
            Stage.QUYISH,
            Stage.APARAT,
            Stage.YUVISH,
            Stage.SARTAROFKA,
            Stage.UPAKOVKA,
            Stage.OMBOR,
            Stage.JONATISH,
            Stage.DONE,
        ]
        if self.needs_matte():
            base.insert(base.index(Stage.SARTAROFKA), Stage.MATIVIY)
        return base

    def next_stage(self):
        f = self.flow()
        try:
            i = f.index(self.stage)
        except ValueError:
            return Stage.QABUL
        return f[min(i + 1, len(f) - 1)]


# =========================
# APARATLAR
# =========================
class Machine(models.Model):
    code = models.CharField(_("Aparat kodi"), max_length=10, unique=True)  # A1..D4
    status = models.CharField(_("Holati"), max_length=20, choices=MachineStatus.choices, default=MachineStatus.IDLE)

    current_batch = models.ForeignKey(
        "Batch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="running_on",
        verbose_name=_("Hozirgi batch"),
    )
    busy_since = models.DateTimeField(_("Band bo'lgan vaqti"), null=True, blank=True)

    class Meta:
        verbose_name = _("Aparat")
        verbose_name_plural = _("Aparatlar")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.status})"


# =========================
# SPLIT: BATCH
# =========================
class Batch(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="batches", verbose_name=_("Zakaz"))

    title = models.CharField(_("Batch nomi"), max_length=50, default="Batch")
    kg_plan = models.DecimalField(_("Batch kg (reja)"), max_digits=10, decimal_places=2, default=0)
    list_plan = models.PositiveIntegerField(_("Batch list (reja)"), default=0)

    kg_done = models.DecimalField(_("Tayyor kg"), max_digits=10, decimal_places=2, default=0)
    list_done = models.PositiveIntegerField(_("Tayyor list"), default=0)

    stage = models.CharField(_("Bosqich"), max_length=20, choices=Stage.choices, default=Stage.QABUL)

    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Aparat"))

    is_done = models.BooleanField(_("Tugadi"), default=False)
    is_paused = models.BooleanField(_("To'xtatilgan"), default=False)

    created_at = models.DateTimeField(_("Yaratilgan"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan"), auto_now=True)

    class Meta:
        verbose_name = _("Batch")
        verbose_name_plural = _("Batchlar")
        ordering = ["-id"]

    def __str__(self):
        return f"Batch#{self.id} ({self.order_id}) {self.title}"

    def can_advance(self) -> bool:
        return (not self.is_paused) and self.is_done

    def advance(self):
        # Batch keyingi bosqichga o‘tadi
        self.stage = self.order.next_stage()
        self.is_done = False
        self.machine = None
        self.save()


# =========================
# YUVISH (W1..W5) + LOAD
# =========================
class WashingMachine(models.Model):
    code = models.CharField(_("Yuvish kodi"), max_length=10, unique=True)  # W1..W5

    class Meta:
        verbose_name = _("Yuvish apparati")
        verbose_name_plural = _("Yuvish apparatlari")
        ordering = ["code"]

    def __str__(self):
        return self.code


class WashingLoad(models.Model):
    machine = models.ForeignKey(WashingMachine, on_delete=models.PROTECT, verbose_name=_("Yuvish apparati"))
    started_at = models.DateTimeField(_("Boshladi"), null=True, blank=True)
    finished_at = models.DateTimeField(_("Tugadi"), null=True, blank=True)
    is_done = models.BooleanField(_("Yakunlandi"), default=False)

    class Meta:
        verbose_name = _("Yuvish load")
        verbose_name_plural = _("Yuvish loadlar")
        ordering = ["-id"]

    def __str__(self):
        return f"Load#{self.id} ({self.machine.code})"

    def start(self):
        if not self.started_at:
            self.started_at = timezone.now()
            self.save(update_fields=["started_at"])

    def finish(self):
        self.is_done = True
        self.finished_at = timezone.now()
        self.save(update_fields=["is_done", "finished_at"])

        # load ichidagi batchlar keyingi bosqichga o‘tadi
        for item in self.items.select_related("batch", "batch__order").all():
            b = item.batch
            b.is_done = True
            b.advance()  # next stage
            StageLog.objects.create(order=b.order, batch=b, from_stage=Stage.YUVISH, to_stage=b.stage, note="Yuvish yakunlandi")


class WashingLoadItem(models.Model):
    load = models.ForeignKey(WashingLoad, on_delete=models.CASCADE, related_name="items")
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Load item")
        verbose_name_plural = _("Load itemlar")
        unique_together = [("load", "batch")]

    def __str__(self):
        return f"{self.load} -> {self.batch}"


# =========================
# UPAKOVKA / OMBOR / JO'NATISH
# =========================
class PackingLot(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="packing_lots", verbose_name=_("Zakaz"))
    packs = models.PositiveIntegerField(_("Pachka"), default=0)
    kg = models.DecimalField(_("Kg"), max_digits=10, decimal_places=2, default=0)
    pcs = models.PositiveIntegerField(_("Dona"), default=0)
    created_at = models.DateTimeField(_("Yaratilgan"), auto_now_add=True)

    class Meta:
        verbose_name = _("Upakovka lot")
        verbose_name_plural = _("Upakovka lotlar")
        ordering = ["-id"]

    def __str__(self):
        return f"PackingLot#{self.id} (Zakaz#{self.order_id})"


class Location(models.Model):
    code = models.CharField(_("Joy (location)"), max_length=20, unique=True)  # A-3-2

    class Meta:
        verbose_name = _("Joy")
        verbose_name_plural = _("Joylar")
        ordering = ["code"]

    def __str__(self):
        return self.code


class WarehouseLot(models.Model):
    lot_code = models.CharField(_("Lot kodi"), max_length=30, unique=True)  # WH-YYYY-xxxxx
    packing_lot = models.ForeignKey(PackingLot, on_delete=models.PROTECT, related_name="warehouse_lots")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)

    packs_total = models.PositiveIntegerField(default=0)
    pcs_total = models.PositiveIntegerField(default=0)
    kg_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    packs_left = models.PositiveIntegerField(default=0)
    pcs_left = models.PositiveIntegerField(default=0)
    kg_left = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Ombor lot")
        verbose_name_plural = _("Ombor lotlar")
        ordering = ["-id"]

    def __str__(self):
        return self.lot_code

    def set_totals_from_packing(self):
        self.packs_total = self.packing_lot.packs
        self.pcs_total = self.packing_lot.pcs
        self.kg_total = self.packing_lot.kg
        self.packs_left = self.packs_total
        self.pcs_left = self.pcs_total
        self.kg_left = self.kg_total


class Shipment(models.Model):
    customer = models.CharField(_("Kimga jo'natildi"), max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Jo'natish")
        verbose_name_plural = _("Jo'natishlar")
        ordering = ["-id"]

    def __str__(self):
        return f"Shipment#{self.id}"


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="items")
    lot = models.ForeignKey(WarehouseLot, on_delete=models.PROTECT)

    packs = models.PositiveIntegerField(default=0)
    pcs = models.PositiveIntegerField(default=0)
    kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Jo'natish item")
        verbose_name_plural = _("Jo'natish itemlar")

    def __str__(self):
        return f"{self.shipment} -> {self.lot}"

    def apply(self):
        # qisman jo'natish: ombor qoldig'idan kamaytirish
        self.lot.packs_left = max(0, self.lot.packs_left - self.packs)
        self.lot.pcs_left = max(0, self.lot.pcs_left - self.pcs)
        self.lot.kg_left = max(0, self.lot.kg_left - self.kg)
        self.lot.save(update_fields=["packs_left", "pcs_left", "kg_left"])


# =========================
# NOSOZLIK (A variant)
# =========================
class Ticket(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name="tickets")
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)

    title = models.CharField(_("Muammo nomi"), max_length=200)
    comment = models.TextField(_("Izoh"), blank=True, default="")
    photo = models.ImageField(_("Foto"), upload_to="tickets/", blank=True, null=True)

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Nosozlik ticket")
        verbose_name_plural = _("Nosozlik ticketlar")
        ordering = ["-id"]

    def __str__(self):
        return f"Ticket#{self.id} {self.machine.code} {self.status}"


# =========================
# LOG
# =========================
class StageLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="logs")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs")
    from_stage = models.CharField(max_length=20, blank=True, default="")
    to_stage = models.CharField(max_length=20, choices=Stage.choices)
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Bosqich log")
        verbose_name_plural = _("Bosqich loglar")
        ordering = ["-id"]

    def __str__(self):
        return f"#{self.order_id} {self.from_stage} -> {self.to_stage}"

