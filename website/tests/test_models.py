from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
from website.models import Page, LogEntry, LogAsset, PageAsset

# Create a temporary directory for media files during tests
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ModelTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_page(self):
        page = Page.objects.create(title="Words", slug="words", content_markdown="Some text")
        self.assertEqual(str(page), "Words")

    def test_create_log_entry(self):
        entry = LogEntry.objects.create(
            title="230919-bear", 
            slug="230919-bear", 
            content_markdown="Content", 
            publish_date=timezone.now()
        )
        self.assertEqual(str(entry), "230919-bear")

    def test_create_log_asset_custom_filename(self):
        # We need a LogEntry first
        entry = LogEntry.objects.create(
            title="230919-bear", 
            slug="230919-bear", 
            content_markdown="Content", 
            publish_date=timezone.now()
        )
        # Create a temp file to upload
        file_content = b"fake image content"
        uploaded_file = SimpleUploadedFile("test_image.jpg", file_content, content_type="image/jpeg")
        
        asset = LogAsset.objects.create(
            log_entry=entry,
            file=uploaded_file,
            custom_filename="custom_bear.jpg"
        )
        # Check custom filename logic
        self.assertTrue(asset.file.name.endswith("custom_bear.jpg"))

    def test_create_log_asset_auto_filename(self):
        entry = LogEntry.objects.create(
            title="230919-bear", 
            slug="230919-bear", 
            content_markdown="Content", 
            publish_date=timezone.now()
        )
        file_content = b"fake image content"
        uploaded_file_1 = SimpleUploadedFile("test_image.jpg", file_content, content_type="image/jpeg")
        uploaded_file_2 = SimpleUploadedFile("another_image.jpg", file_content, content_type="image/jpeg")
        
        asset1 = LogAsset.objects.create(
            log_entry=entry,
            file=uploaded_file_1
        )
        asset2 = LogAsset.objects.create(
            log_entry=entry,
            file=uploaded_file_2
        )
        
        import re
        self.assertTrue(re.match(r"^log_assets/230919-bear-[0-9a-f]{8}\.jpg$", asset1.file.name))
        self.assertTrue(re.match(r"^log_assets/230919-bear-[0-9a-f]{8}\.jpg$", asset2.file.name))

    def test_create_log_asset_path_traversal(self):
        entry = LogEntry.objects.create(
            title="230919-bear", 
            slug="230919-bear", 
            content_markdown="Content", 
            publish_date=timezone.now()
        )
        file_content = b"fake image content"
        uploaded_file = SimpleUploadedFile("test_image.jpg", file_content, content_type="image/jpeg")
        
        asset = LogAsset.objects.create(
            log_entry=entry,
            file=uploaded_file,
            custom_filename="../../test_path_traversal.jpg"
        )
        # Check that it is sanitized and stored inside log_assets folder
        self.assertEqual(os.path.basename(asset.file.name), "test_path_traversal.jpg")
        self.assertTrue(asset.file.name.startswith("log_assets/"))

    def test_create_page_asset_auto_filename(self):
        page = Page.objects.create(title="Performances", slug="performances", content_markdown="Some text")
        file_content = b"fake image content"
        uploaded_file = SimpleUploadedFile("performance.jpg", file_content, content_type="image/jpeg")
        
        asset = PageAsset.objects.create(
            page=page,
            file=uploaded_file
        )
        
        import re
        self.assertTrue(re.match(r"^page_assets/performances-[0-9a-f]{8}\.jpg$", asset.file.name))
