import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.base import ContentFile
from django.test import SimpleTestCase, override_settings

from apps.m365.graph_client import GRAPH_BASE, GraphAPIError, GraphClient
from apps.m365.storage import ConfiguredStorage, SharePointStorage, get_storage
from apps.common.uploads import upload_to_dispatches


class ConfiguredStorageTests(SimpleTestCase):
    def test_graph_lookup_failure_aborts_save_before_upload(self):
        storage = SharePointStorage('Documents')
        storage.client = Mock()
        storage.client.exists.side_effect = GraphAPIError('Temporary lookup failure')
        with self.assertRaises(GraphAPIError):
            storage.save('existing.pdf', ContentFile(b'replacement'))
        storage.client.upload_file.assert_not_called()

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

    def test_dispatch_files_route_by_direction_and_legacy_paths_remain_readable(self):
        folders = {
            "dispatches": "CongVan", "incoming_docs": "CongVanDen", "outgoing_docs": "CongVanDi",
        }
        prefixes = {
            "dispatches": "dispatches", "incoming_docs": "incoming_docs", "outgoing_docs": "outgoing_docs",
        }
        storage = get_storage("dispatches")
        with override_settings(M365_FOLDER_MAP=folders, M365_UPLOAD_PREFIX_MAP=prefixes):
            for dispatch_type, prefix, folder in (
                ("Incoming", "incoming_docs", "CongVanDen"),
                ("Outgoing", "outgoing_docs", "CongVanDi"),
                ("InternalDirective", "dispatches", "CongVan"),
            ):
                with self.subTest(dispatch_type=dispatch_type):
                    generated = upload_to_dispatches(SimpleNamespace(dispatch_type=dispatch_type), "van-ban.pdf")
                    self.assertTrue(generated.startswith(prefix + "/"))
                    self.assertTrue(storage._remote_name(generated).startswith(folder + "/"))
                    self.assertEqual(storage._remote_name(f"{folder}/2026/09/van-ban.pdf"), f"{folder}/2026/09/van-ban.pdf")
            self.assertEqual(storage._remote_name("dispatches/2026/09/old.pdf"), "CongVan/2026/09/old.pdf")
            self.assertEqual(storage._remote_name("CongVan/2026/09/old.pdf"), "CongVan/2026/09/old.pdf")

    def test_dispatch_save_uses_direction_folder_and_old_name_still_opens(self):
        storage = get_storage("dispatches")
        with override_settings(
            M365_STORAGE_ENABLED=True,
            M365_SHAREPOINT_LIBRARY="Documents",
            M365_FOLDER_MAP={"dispatches": "CongVan", "incoming_docs": "CongVanDen", "outgoing_docs": "CongVanDi"},
            M365_UPLOAD_PREFIX_MAP={"dispatches": "dispatches", "incoming_docs": "incoming_docs", "outgoing_docs": "outgoing_docs"},
        ), patch("apps.m365.storage.SharePointStorage") as backend_class:
            backend = backend_class.return_value
            backend.exists.return_value = False
            for dispatch_type, folder in (("Incoming", "CongVanDen"), ("Outgoing", "CongVanDi")):
                with self.subTest(dispatch_type=dispatch_type):
                    path = upload_to_dispatches(SimpleNamespace(dispatch_type=dispatch_type), "van-ban.pdf")
                    saved = storage.save(path, ContentFile(b"test", name="van-ban.pdf"))
                    self.assertTrue(saved.startswith(folder + "/"))
                    self.assertEqual(backend._save.call_args.args[0], saved)
            storage.open("CongVan/2026/09/old.pdf")
            backend._open.assert_called_with("CongVan/2026/09/old.pdf", "rb")


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
