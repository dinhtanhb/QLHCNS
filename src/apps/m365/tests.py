import tempfile

from django.core.files.base import ContentFile
from django.test import SimpleTestCase, override_settings

from apps.m365.graph_client import GRAPH_BASE, GraphClient
from apps.m365.storage import ConfiguredStorage, get_storage


class ConfiguredStorageTests(SimpleTestCase):
    def test_deconstruction_does_not_depend_on_m365_toggle(self):
        folders = {"documents": "", "dispatches": "CongVan"}
        with override_settings(M365_STORAGE_ENABLED=False, M365_FOLDER_MAP=folders):
            local_state = get_storage("documents").deconstruct()
        with override_settings(M365_STORAGE_ENABLED=True, M365_FOLDER_MAP=folders):
            sharepoint_state = get_storage("documents").deconstruct()

        self.assertIsInstance(get_storage("documents"), ConfiguredStorage)
        self.assertEqual(local_state, sharepoint_state)

    def test_disabled_backend_round_trips_file_locally(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(
                M365_STORAGE_ENABLED=False,
                MEDIA_ROOT=media_root,
                M365_FOLDER_MAP={},
            ):
                storage = get_storage("documents")
                saved_name = storage.save("test.txt", ContentFile(b"IHRMS"))

                with storage.open(saved_name, "rb") as stored_file:
                    self.assertEqual(stored_file.read(), b"IHRMS")

    def test_feature_folder_prefix_is_applied_once(self):
        storage = get_storage("dispatches")
        with override_settings(
            M365_FOLDER_MAP={"dispatches": "CongVan"},
            M365_UPLOAD_PREFIX_MAP={"dispatches": "dispatches"},
        ):
            self.assertEqual(storage._remote_name("dispatches/2026/09/file.txt"), "CongVan/2026/09/file.txt")
            self.assertEqual(storage._remote_name("CongVan/2026/09/file.txt"), "CongVan/2026/09/file.txt")


class GraphClientFolderTests(SimpleTestCase):
    def test_item_content_url_has_single_path_delimiter(self):
        client = GraphClient()
        client._drive_id = lambda library_name: "drive-id"

        self.assertEqual(
            client._item_url("Documents", "folder/file.txt", ":/content"),
            f"{GRAPH_BASE}/drives/drive-id/root:/folder/file.txt:/content",
        )

    def test_upload_creates_each_missing_parent_folder(self):
        client = GraphClient()
        calls = []
        client._drive_id = lambda library_name: "drive-id"
        client._request = lambda method, url, **kwargs: calls.append((method, url, kwargs))

        client._ensure_parent_folders("Documents", "CongVan/dispatches/2026/file.txt")

        self.assertEqual([call[0] for call in calls], ["POST", "POST", "POST"])
        self.assertTrue(calls[0][1].endswith("/root/children"))
        self.assertTrue(calls[1][1].endswith("/root:/CongVan:/children"))
        self.assertEqual(calls[2][2]["json"]["name"], "2026")

    def test_send_mail_uses_graph_mailbox_endpoint_and_pdf_attachments(self):
        client = GraphClient()
        calls = []
        client._request = lambda method, url, **kwargs: calls.append((method, url, kwargs))

        client.send_mail(
            "ihrms@example.org", "director@example.org", "Xin duyệt", "Nội dung",
            [{"name": "proposal.pdf", "content_type": "application/pdf", "content": b"PDF"}],
        )

        method, url, kwargs = calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/users/ihrms@example.org/sendMail"))
        attachment = kwargs["json"]["message"]["attachments"][0]
        self.assertEqual(attachment["name"], "proposal.pdf")
        self.assertEqual(attachment["contentBytes"], "UERG")
