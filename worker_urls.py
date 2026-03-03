from django.urls import path
from . import views_worker as v

urlpatterns = [
    path("login/", v.worker_login, name="worker_login"),
    path("logout/", v.worker_logout, name="worker_logout"),

    path("", v.worker_dashboard, name="worker_dashboard"),
    path("batch/<int:batch_id>/", v.batch_detail, name="batch_detail"),
    path("batch/<int:batch_id>/assign-machine/", v.assign_machine, name="assign_machine"),
    path("batch/<int:batch_id>/done/", v.done_and_next, name="done_and_next"),
]