from django.contrib import admin
from .models import NewsArticle, UserVerification, ScrapingLog


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display  = ['title', 'category', 'source_name', 'authenticity', 'confidence_score', 'scraped_date', 'is_active']
    list_filter   = ['category', 'source_name', 'authenticity', 'is_active', 'scraped_date']
    search_fields = ['title', 'content', 'source_name']
    readonly_fields   = ['scraped_date', 'confidence_score']
    list_editable = ['is_active']
    list_per_page = 25
    ordering      = ['-scraped_date']
    fieldsets = (
        ('Article', {'fields': ('title', 'content', 'category')}),
        ('Source',  {'fields': ('source_name', 'source_url', 'published_date')}),
        ('AI Verdict', {'fields': ('authenticity', 'confidence_score')}),
        ('Status',  {'fields': ('is_active', 'scraped_date')}),
    )


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display  = ['_preview', 'result', 'confidence_score', 'submitted_at', 'ip_address']
    list_filter   = ['result', 'submitted_at']
    search_fields = ['title', 'content']
    readonly_fields   = ['submitted_at', 'result', 'confidence_score', 'ip_address']
    list_per_page = 25
    ordering      = ['-submitted_at']
    fieldsets = (
        ('Content',         {'fields': ('title', 'content')}),
        ('Verification',    {'fields': ('result', 'confidence_score')}),
        ('Metadata',        {'fields': ('submitted_at', 'ip_address')}),
    )

    @admin.display(description='Title / Content')
    def _preview(self, obj):
        text = obj.title or obj.content
        return text[:60] + '…' if len(text) > 60 else text


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display  = ['started_at', 'status', 'triggered_by', 'articles_saved', 'articles_skipped', 'articles_errors', 'duration_seconds']
    list_filter   = ['status', 'triggered_by', 'started_at']
    readonly_fields   = ['started_at', 'finished_at', 'articles_saved', 'articles_skipped', 'articles_errors', 'error_msg']
    list_per_page = 30
    ordering      = ['-started_at']


# Admin site branding
admin.site.site_header  = "InfoTrust Administration"
admin.site.site_title   = "InfoTrust Admin"
admin.site.index_title  = "InfoTrust Control Panel"
