from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("files/<str:token>/", views.sharepoint_file, name="sharepoint_file"),
    path("api/history/", views.api_history, name="api_history"),
    path("", views.assistant_page, name="assistant_page"),
    path("api/search/", views.api_search, name="api_search"),
]
