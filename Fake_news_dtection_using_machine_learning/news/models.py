from django.db import models
from django.utils import timezone

class NewsArticle(models.Model):
    """Model for storing scraped news articles"""
    CATEGORY_CHOICES = [
        ('politics', 'Politics'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('health', 'Health'),
        ('science', 'Science'),
        ('world', 'World'),
        ('other', 'Other'),
    ]

    AUTHENTICITY_CHOICES = [
        ('real', 'Real'),
        ('fake', 'Fake'),
        ('unverified', 'Unverified'),
    ]

    title = models.CharField(max_length=500)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    source_name = models.CharField(max_length=200)
    source_url = models.URLField(max_length=1000)
    published_date = models.DateTimeField(null=True, blank=True)
    scraped_date = models.DateTimeField(auto_now_add=True)
    authenticity = models.CharField(max_length=20, choices=AUTHENTICITY_CHOICES, default='unverified')
    confidence_score = models.FloatField(null=True, blank=True, help_text="Model confidence score (0-1)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-scraped_date']
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'

    def __str__(self):
        return f"{self.title[:50]}... ({self.source_name})"


class UserVerification(models.Model):
    """Model for storing user-submitted news for verification"""
    RESULT_CHOICES = [
        ('fake', 'Fake'),
        ('real', 'Real'),
    ]

    title = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    confidence_score = models.FloatField(help_text="Model confidence score (0-1)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'User Verification'
        verbose_name_plural = 'User Verifications'

    def __str__(self):
        return f"Verification - {self.result.upper()} ({self.confidence_score:.2%})"


class ScrapingLog(models.Model):
    """
    Tracks every auto-scrape run (Celery Beat or manual trigger).
    Visible on the Statistics page as a live activity feed.
    """
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed',  'Failed'),
    ]
    TRIGGER_CHOICES = [
        ('celery_beat', 'Scheduled (Celery Beat)'),
        ('manual',      'Manual'),
    ]

    status           = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')
    triggered_by     = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='celery_beat')
    started_at       = models.DateTimeField(auto_now_add=True)
    finished_at      = models.DateTimeField(null=True, blank=True)
    articles_saved   = models.IntegerField(default=0)
    articles_skipped = models.IntegerField(default=0)
    articles_errors  = models.IntegerField(default=0)
    error_msg        = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Scraping Log'
        verbose_name_plural = 'Scraping Logs'

    def __str__(self):
        return f"[{self.triggered_by}] {self.status} — {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def duration_seconds(self):
        if self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds(), 1)
        return None
