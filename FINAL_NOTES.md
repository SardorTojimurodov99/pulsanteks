# Pulsanteks final patch

## Muhim
Bu patch **kodlarni bir-biriga moslab** yig'ildi va Python sintaksisi bo'yicha tekshirildi.
Django paketi bu muhitda o'rnatilmaganligi sabab `manage.py check` bu yerda ishga tushirilmadi.

## Sizda bajariladigan buyruqlar
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_machines
python manage.py check
python manage.py collectstatic --noinput
```

## Asosiy o'zgarishlar
- Zakaz va tarkib formasi final ko'rinishga keltirildi.
- Batch yaratish worker order detail sahifasiga qo'shildi.
- Batch: LIST / BUTTON oqimi qo'shildi.
- Qavat rangi, pantone, sadaf/polegal, qavat izohi, lazer yozuvi qo'shildi.
- Palirofka apparatlari `P1-P6` qo'shildi.
- Apparat pause/resume/broken oqimi qo'shildi.
- Mexanik bo'lim saqlandi.
- Ombor real miqdor / jo'natilgan / qoldiq hisobiga moslashtirildi.
```
