from django.urls import path
from . import views

urlpatterns = [
    path("", views.shipment_list, name="shipment_list"),
    path("create/", views.shipment_create, name="shipment_create"),
    path("<int:pk>/", views.shipment_detail, name="shipment_detail"),
]