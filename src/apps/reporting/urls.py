from django.urls import path
from . import views

app_name = "reporting"

urlpatterns = [
    path("", views.report_dashboard, name="dashboard"),
    path("export/employees/", views.export_employees, name="export_employees"),
    path("export/contracts/", views.export_contracts, name="export_contracts"),
    path("export/dispatches/", views.export_dispatches, name="export_dispatches"),
]
