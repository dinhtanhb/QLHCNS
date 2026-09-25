from django.urls import path

from apps.activity.views import activity_dashboard


app_name = "activity"

urlpatterns = [
    path("", activity_dashboard, name="dashboard"),
]
