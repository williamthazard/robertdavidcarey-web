from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Page, LogEntry, LogAsset

class LogAssetInline(admin.TabularInline):
    model = LogAsset
    extra = 1
    fields = ('file', 'custom_filename', 'copyable_snippet')
    readonly_fields = ('copyable_snippet',)

    def copyable_snippet(self, instance):
        if instance.file:
            url = instance.file.url
            # Display helpful, copyable code tags for images/videos in admin
            return mark_safe(
                f'<code style="background:#eee; padding:2px 5px;">{url}</code>'
            )
        return "Save model to see snippet"
    copyable_snippet.short_description = "Media URL Snippet"

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date')
    search_fields = ('title', 'content_markdown')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LogAssetInline]

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
