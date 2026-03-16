from django.urls import path

from . import views, views_worker

urlpatterns = [
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/<int:pk>/", views.batch_detail, name="batch_detail"),
    path("batches/<int:pk>/advance/", views.batch_advance, name="batch_advance"),

    path("worker/", views_worker.worker_dashboard, name="worker_dashboard"),
    path("worker/order/<int:pk>/", views_worker.worker_order_detail, name="worker_order_detail"),
    path("worker/order/<int:pk>/accept/", views_worker.worker_order_accept, name="worker_order_accept"),
    path("worker/order/<int:pk>/finish/", views_worker.worker_order_finish, name="worker_order_finish"),
    path("worker/order/<int:pk>/batch/", views_worker.worker_create_batch, name="worker_create_batch"),

    path("worker/batch/<int:pk>/", views_worker.worker_batch_detail, name="worker_batch_detail"),
    path("worker/batch/<int:pk>/accept/", views_worker.worker_accept, name="worker_accept"),
    path("worker/batch/<int:pk>/finish/", views_worker.worker_finish, name="worker_finish"),

    path("machines/", views_worker.machine_panel, name="machine_panel"),
    path("machines/<int:machine_id>/", views_worker.machine_detail, name="machine_detail"),
    path("machines/<int:machine_id>/start/", views_worker.machine_start, name="machine_start"),
    path("machines/<int:machine_id>/pause/", views_worker.machine_pause, name="machine_pause"),
    path("machines/<int:machine_id>/resume/", views_worker.machine_resume, name="machine_resume"),
    path("machines/<int:machine_id>/finish/", views_worker.machine_finish, name="machine_finish"),
    path("machines/<int:machine_id>/broken/", views_worker.machine_broken, name="machine_broken"),

    path("mechanic/", views_worker.mechanic_dashboard, name="mechanic_dashboard"),
    path("mechanic/<int:breakdown_id>/accept/", views_worker.mechanic_accept, name="mechanic_accept"),
    path("mechanic/<int:breakdown_id>/fix/", views_worker.mechanic_fix, name="mechanic_fix"),
]
