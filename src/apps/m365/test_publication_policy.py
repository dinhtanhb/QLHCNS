"""New media is private draft; authenticated readers see published only."""
from django.test import override_settings
from apps.portal import tests_review_20261008 as fixtures
from apps.m365.models import CompanyMedia
from apps.security.data_access import can_read_file


@override_settings(AXES_ENABLED=False)
class MediaPublicationPolicyTests(fixtures.Review20261008Fixtures):
    def test_new_media_is_draft_and_file_read_requires_publication_for_ordinary_users(self):
        reader=self.make_user('EMPLOYEE',self.make_employee('MEDIA-C-EMP'),'media-c-reader')
        manager=self.make_user('HR_MANAGER',self.make_employee('MEDIA-C-HR'),'media-c-manager')
        item=CompanyMedia.objects.create(title='Synthetic draft',media_type='Image',file='synthetic/media-c.png',created_by=manager)
        self.assertFalse(can_read_file(reader,item))
        self.assertTrue(can_read_file(manager,item))
        self.assertEqual(item.status,'Draft')

    def test_published_media_visible_and_admin_scopes_drafts(self):
        from django.contrib import admin
        from django.test import RequestFactory
        from apps.security.data_access import visible_company_media_for
        reader=self.make_user('SYS_ADMIN',self.make_employee('MEDIA-C-SYS'),'media-c-sys',is_staff=True)
        manager=self.make_user('HR_OFFICER',self.make_employee('MEDIA-C-OFF'),'media-c-officer',is_staff=True)
        draft=CompanyMedia.objects.create(title='Synthetic draft',media_type='Image',file='synthetic/draft.png')
        published=CompanyMedia.objects.create(title='Synthetic published',media_type='Image',file='synthetic/published.png')
        published.status='Published';published.save()
        self.assertEqual(set(visible_company_media_for(reader).values_list('pk',flat=True)),{published.pk})
        self.assertEqual(set(visible_company_media_for(manager).values_list('pk',flat=True)),{draft.pk,published.pk})
        request=RequestFactory().get('/admin/m365/companymedia/');request.user=reader
        self.assertEqual(set(admin.site._registry[CompanyMedia].get_queryset(request).values_list('pk',flat=True)),{published.pk})
