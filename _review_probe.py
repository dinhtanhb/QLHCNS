"""Temporary review probe - verifies model-level validation findings."""
import os
import sys
from datetime import datetime

os.environ.update(
    DJANGO_SETTINGS_MODULE="config.settings",
    SECRET_KEY="probe-only-key-0123456789abcdefghijklmnopqrstuvwxyz-ABCDEFG",
    DB_ENGINE="django.db.backends.sqlite3",
    DEBUG="False",
    APP_ENV="test",
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import django

django.setup()

from django.core.exceptions import ValidationError

from apps.office.models import VehicleBooking, RoomBooking


def probe(label, instance):
    try:
        instance.clean_fields()
        print(f"[OK]   {label}: clean_fields passed")
    except ValidationError as error:
        print(f"[FAIL] {label}: ValidationError -> {error.message_dict}")


print("VehicleBooking.STATUS_CHOICES =", VehicleBooking.STATUS_CHOICES)
print("RoomBooking.STATUS_CHOICES    =", RoomBooking.STATUS_CHOICES)
print()

probe(
    "VehicleBooking(status='Pending') as created by portal view",
    VehicleBooking(
        vehicle_id=1,
        employee_id=1,
        destination="Hanoi",
        start_time=datetime(2026, 3, 2, 9, 0),
        end_time=datetime(2026, 3, 2, 10, 0),
        status="Pending",
    ),
)

probe(
    "RoomBooking(status='Pending') as created by portal view",
    RoomBooking(
        room_id=1,
        employee_id=1,
        purpose="Hop",
        start_time=datetime(2026, 3, 2, 9, 0),
        end_time=datetime(2026, 3, 2, 10, 0),
        status="Pending",
    ),
)
