from django.urls import path
from . import views

urlpatterns = [
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/<int:pk>/", views.batch_detail, name="batch_detail"),
    path("batches/<int:pk>/advance/", views.batch_advance, name="batch_advance"),
]