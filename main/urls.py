from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# main/worker_urls.py
from django.urls import path
from . import worker_views

app_name = "worker"

urlpatterns = [
    path("", worker_views.dashboard, name="dashboard"),
    path("batch/<int:pk>/", worker_views.batch_detail, name="batch_detail"),
    path("batch/<int:pk>/update/", worker_views.batch_update, name="batch_update"),
    path("batch/<int:pk>/pause/", worker_views.batch_pause, name="batch_pause"),
    path("batch/<int:pk>/done/", worker_views.batch_done, name="batch_done"),
]