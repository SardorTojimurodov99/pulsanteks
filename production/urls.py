from django.urls import path
from . import views
from . import views_worker

urlpatterns = [
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/<int:pk>/", views.batch_detail, name="batch_detail"),
    path("batches/<int:pk>/advance/", views.batch_advance, name="batch_advance"),

    path("worker/", views_worker.worker_dashboard, name="worker_dashboard"),
    path("worker/batch/<int:pk>/", views_worker.worker_batch_detail, name="worker_batch_detail"),
    path("worker/batch/<int:pk>/done/", views_worker.worker_done, name="worker_done"),
]