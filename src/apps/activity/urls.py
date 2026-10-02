from django.urls import path

from apps.activity.views import activity_calendar, activity_create, activity_dashboard, activity_update


app_name = "activity"

urlpatterns = [
    path("", activity_dashboard, name="dashboard"),
    path("create/", activity_create, name="create"),
    path("calendar/", activity_calendar, name="calendar"),
    path("<int:pk>/edit/", activity_update, name="update"),
]
