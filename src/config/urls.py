from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import Http404
from apps.security.files import private_file


def block_raw_media(request, name):
    raise Http404

urlpatterns = [
    path('api/mobile/v1/', include('apps.mobile.urls')),
    path('private-files/<path:name>', private_file, name='private_file'),
    path('media/<path:name>', block_raw_media),
    path("", RedirectView.as_view(url="/portal/", permanent=False)),
    path("admin/", admin.site.urls),
    path("portal/", include("apps.portal.urls")),
    path("reports/", include("apps.reporting.urls")),
    path("assistant/", include("apps.assistant.urls")),
]
