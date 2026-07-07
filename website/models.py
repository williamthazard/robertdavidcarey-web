import os
import uuid
import threading
from django.db import models

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Page(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="Used in the URL (e.g. 'words', 'sounds').")
    content_markdown = models.TextField(help_text="Raw Markdown content.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PageAsset(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='assets')
    file = models.FileField(upload_to='page_assets/')
    custom_filename = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Optional: Rename file (e.g. 'performance.jpg'). Leave blank to auto-rename based on page slug."
    )

    def __str__(self):
        return os.path.basename(self.file.name) if self.file else f"PageAsset #{self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            old_path = self.file.path
            ext = os.path.splitext(self.file.name)[1].lower()
            
            if self.custom_filename:
                from django.utils.text import get_valid_filename
                cleaned_name = get_valid_filename(os.path.basename(self.custom_filename))
                new_name = cleaned_name
                if not new_name.endswith(ext):
                    new_name = os.path.splitext(new_name)[0] + ext
            else:
                import uuid
                suffix = uuid.uuid4().hex[:8]
                new_name = f"{self.page.slug}-{suffix}{ext}"
            
            new_relative_path = os.path.join('page_assets', new_name)
            new_absolute_path = os.path.join(os.path.dirname(old_path), new_name)
            
            if old_path != new_absolute_path:
                if old_path.lower() == new_absolute_path.lower():
                    temp_path = old_path + '.tmp_rename'
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    os.rename(old_path, temp_path)
                    os.rename(temp_path, new_absolute_path)
                else:
                    if os.path.exists(new_absolute_path):
                        os.remove(new_absolute_path)
                    os.rename(old_path, new_absolute_path)
                self.file.name = new_relative_path
                super().save(update_fields=['file'])


class LogEntry(models.Model):
    title = models.CharField(max_length=200, help_text="E.g., 'bear' or '240809'")
    slug = models.SlugField(unique=True, help_text="E.g., '230919-bear' or '240809'")
    content_markdown = models.TextField(help_text="Raw Markdown content.")
    publish_date = models.DateTimeField(help_text="Publish date of the entry.")
    send_email_notification = models.BooleanField(
        default=False,
        help_text="Send email newsletter to all subscribers on save."
    )
    email_sent = models.BooleanField(
        default=False,
        help_text="Indicates if email was already sent for this entry."
    )

    class Meta:
        ordering = ['-publish_date']
        verbose_name_plural = "Log Entries"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.send_email_notification and not self.email_sent:
            import sys
            if 'test' not in sys.argv:
                threading.Thread(target=self.send_newsletter_emails).start()

    def send_newsletter_emails(self):
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        from website.templatetags.markdown_filters import render_markdown
        import re
        
        subscribers = list(Subscriber.objects.all())
        if not subscribers:
            LogEntry.objects.filter(pk=self.pk).update(email_sent=True)
            return

        subject = f"New log entry: {self.title}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'robertdavidcarey@pm.me')
        domain = "https://robertdavidcarey.com"
        
        # 1. Process HTML Content
        raw_html = render_markdown(self.content_markdown)
        absolute_html = raw_html
        absolute_html = absolute_html.replace('src="/media/', f'src="{domain}/media/')
        absolute_html = absolute_html.replace('href="/media/', f'href="{domain}/media/')
        absolute_html = re.sub(r'href="/([^"]*)"', rf'href="{domain}/\1"', absolute_html)
        
        # 2. Process Plain Text Content
        absolute_text = self.content_markdown
        absolute_text = absolute_text.replace('](/media/', f']({domain}/media/')
        absolute_text = re.sub(r'\]\(/([^)]*)\)', rf']({domain}/\1)', absolute_text)
        
        for sub in subscribers:
            unsub_link = f"https://robertdavidcarey.com/unsubscribe/{sub.token}/"
            
            context = {
                'entry': self,
                'html_content': absolute_html,
                'text_content': absolute_text,
                'unsubscribe_link': unsub_link,
            }
            
            message_text = render_to_string('emails/newsletter.txt', context)
            message_html = render_to_string('emails/newsletter.html', context)
            
            try:
                send_mail(
                    subject=subject,
                    message=message_text,
                    from_email=from_email,
                    recipient_list=[sub.email],
                    html_message=message_html,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error sending newsletter to {sub.email}: {e}")
                
        LogEntry.objects.filter(pk=self.pk).update(email_sent=True)


class LogAsset(models.Model):
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name='assets')
    file = models.FileField(upload_to='log_assets/')
    custom_filename = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Optional: Rename file (e.g. 'glow.mp4'). Leave blank to auto-rename based on log slug."
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.file:
            old_path = self.file.path
            ext = os.path.splitext(self.file.name)[1].lower()
            
            if self.custom_filename:
                from django.utils.text import get_valid_filename
                cleaned_name = get_valid_filename(os.path.basename(self.custom_filename))
                new_name = cleaned_name
                if not new_name.endswith(ext):
                    new_name = os.path.splitext(new_name)[0] + ext
            else:
                import uuid
                suffix = uuid.uuid4().hex[:8]
                new_name = f"{self.log_entry.slug}-{suffix}{ext}"
            
            new_relative_path = os.path.join('log_assets', new_name)
            new_absolute_path = os.path.join(os.path.dirname(old_path), new_name)
            
            if old_path != new_absolute_path:
                if old_path.lower() == new_absolute_path.lower():
                    temp_path = old_path + '.tmp_rename'
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    os.rename(old_path, temp_path)
                    os.rename(temp_path, new_absolute_path)
                else:
                    if os.path.exists(new_absolute_path):
                        os.remove(new_absolute_path)
                    os.rename(old_path, new_absolute_path)
                self.file.name = new_relative_path
                super().save(update_fields=['file'])
