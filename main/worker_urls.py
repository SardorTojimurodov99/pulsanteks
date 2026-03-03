from django.urls import path
from . import worker_views

app_name = "worker"

urlpatterns = [
    # bosh sahifa
    path("", worker_views.dashboard, name="dashboard"),

    # batch
    path("batch/<int:pk>/", worker_views.batch_detail, name="batch_detail"),
    path("batch/<int:pk>/update/", worker_views.batch_update, name="batch_update"),
    path("batch/<int:pk>/pause/", worker_views.batch_pause, name="batch_pause"),
    path("batch/<int:pk>/done/", worker_views.batch_done, name="batch_done"),

    # zakaz
    path("zakaz/", worker_views.zakaz_list, name="zakaz_list"),
    path("zakaz/add/", worker_views.zakaz_add, name="zakaz_add"),

    # bo‘limlar (dept)
    path("dept/rang/", worker_views.dept_rang, name="dept_rang"),
    path("dept/quyish/", worker_views.dept_quyish, name="dept_quyish"),
    path("dept/aparat/", worker_views.dept_aparat, name="dept_aparat"),
    path("dept/yuvish/", worker_views.dept_yuvish, name="dept_yuvish"),
    path("dept/mativiy/", worker_views.dept_mativiy, name="dept_mativiy"),
    path("dept/sartarofka/", worker_views.dept_sartarofka, name="dept_sartarofka"),
    path("dept/upakovka/", worker_views.dept_upakovka, name="dept_upakovka"),
    path("dept/ombor/", worker_views.dept_ombor, name="dept_ombor"),
    path("dept/jonatish/", worker_views.dept_jonatish, name="dept_jonatish"),
]