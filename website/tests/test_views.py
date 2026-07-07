import os
import shutil
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.staticfiles import finders
from website.models import Page, LogEntry, Subscriber

@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        Page.objects.create(title="Home", slug="home", content_markdown="Welcome to my homepage")
        Page.objects.create(title="Words", slug="words", content_markdown="My words list")
        LogEntry.objects.create(title="bear", slug="230919-bear", content_markdown="Bear post", publish_date=timezone.now())

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome")

    def test_static_assets_referenced_in_html(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/css/styles.css"')

    def test_static_files_exist_on_disk(self):
        css_path = finders.find('css/styles.css')
        self.assertIsNotNone(css_path)
        self.assertTrue(os.path.exists(css_path))

        font_path = finders.find('fonts/RobotoMono-VariableFont_wght.ttf')
        self.assertIsNotNone(font_path)
        self.assertTrue(os.path.exists(font_path))

    def test_page_view(self):
        response = self.client.get(reverse('page_detail', kwargs={'page_slug': 'words'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My words list")

    def test_log_index(self):
        response = self.client.get(reverse('log_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bear")

    def test_log_detail(self):
        response = self.client.get(reverse('log_detail', kwargs={'entry_slug': '230919-bear'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bear post")

    def test_rss_feed(self):
        response = self.client.get(reverse('rss_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/rss+xml", response.headers.get("Content-Type", ""))
        self.assertContains(response, "log / bear")
        self.assertContains(response, "Bear post")

    def test_subscribe_success(self):
        url = reverse('subscribe')
        response = self.client.post(url, {'email': 'test@example.com'})
        # Should redirect back to log index
        self.assertRedirects(response, reverse('log_index'))
        self.assertTrue(Subscriber.objects.filter(email='test@example.com').exists())

    def test_subscribe_invalid(self):
        url = reverse('subscribe')
        response = self.client.post(url, {'email': 'not-an-email'})
        self.assertRedirects(response, reverse('log_index'))
        self.assertFalse(Subscriber.objects.filter(email='not-an-email').exists())

    def test_unsubscribe(self):
        sub = Subscriber.objects.create(email='test_unsub@example.com')
        token = sub.token
        url = reverse('unsubscribe', kwargs={'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsubscribed Successfully")
        self.assertFalse(Subscriber.objects.filter(email='test_unsub@example.com').exists())

