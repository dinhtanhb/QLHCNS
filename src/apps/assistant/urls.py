from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("", views.assistant_page, name="assistant_page"),
    path("api/search/", views.api_search, name="api_search"),
]
