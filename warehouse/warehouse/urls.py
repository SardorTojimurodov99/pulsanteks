from django.urls import path
from . import views

urlpatterns = [
    path("", views.warehouse_list, name="warehouse_list"),
    path("receive/<int:batch_id>/", views.receive_batch, name="receive_batch"),
]