from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/portal/", permanent=False)),
    path("admin/", admin.site.urls),
    path("portal/", include("apps.portal.urls")),
    path("reports/", include("apps.reporting.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)