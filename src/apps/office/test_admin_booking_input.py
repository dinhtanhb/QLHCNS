"""Booking Admin reports field errors for incomplete timestamps."""
from django.test import override_settings
from django.urls import reverse

from apps.office import tests as fixtures
from apps.office.models import RoomBooking, VehicleBooking
from apps.security.models import User


@override_settings(AXES_ENABLED=False)
class BookingAdminInputTests(fixtures.OfficeTestBase):
    def setUp(self):
        user = User.objects.create_superuser(username='booking-b-admin', password='synthetic-password')
        self.client.force_login(user)

    def payload(self, model):
        return {'room' if model is RoomBooking else 'vehicle': self.room.pk if model is RoomBooking else self.vehicle.pk,
                'employee': self.employee.pk, 'purpose': 'Synthetic booking', 'destination': 'Synthetic destination',
                'start_time_0': '2026-11-02', 'start_time_1': '10:00:00',
                'end_time_0': '2026-11-02', 'end_time_1': '11:00:00', 'status': 'Pending', '_save': 'Save'}

    def test_empty_and_partial_admin_posts_show_field_errors(self):
        for model in (RoomBooking, VehicleBooking):
            url = reverse(f'admin:office_{model._meta.model_name}_add')
            for values in ({}, {'start_time_0': '2026-11-02'}, {'end_time_0': 'bad', 'end_time_1': 'bad'}):
                with self.subTest(model=model.__name__, values=values):
                    response = self.client.post(url, values)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context['adminform'].form.errors)
                    self.assertEqual(model.objects.count(), 0)

    def test_valid_admin_posts_still_save(self):
        for model in (RoomBooking, VehicleBooking):
            with self.subTest(model=model.__name__):
                response = self.client.post(reverse(f'admin:office_{model._meta.model_name}_add'), self.payload(model))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(model.objects.count(), 1)
