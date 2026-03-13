"""
Celery tasks for InfoTrust.
`auto_scrape_news` is scheduled by Celery Beat every hour.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='news.tasks.auto_scrape_news', max_retries=3)
def auto_scrape_news(self):
    """
    Fetch articles from all RSS feeds, verify with AI, save to DB.
    Runs every hour via Celery Beat (crontab minute=0).
    Retries up to 3× on failure with a 5-minute cooldown.
    """
    from .models import NewsArticle, ScrapingLog
    from .news_scraper import NewsScraper
    from .model_predictor import get_predictor

    log = ScrapingLog.objects.create(status='running', triggered_by='celery_beat')

    try:
        articles_raw = NewsScraper().get_sample_news()
        predictor    = get_predictor()
        saved = skipped = errors = 0

        for data in articles_raw:
            try:
                if NewsArticle.objects.filter(title=data['title']).exists():
                    skipped += 1
                    continue

                prediction = predictor.predict(data['content'], data['title'])
                NewsArticle.objects.create(
                    title          = data['title'],
                    content        = data['content'],
                    category       = data['category'],
                    source_name    = data['source_name'],
                    source_url     = data['source_url'],
                    published_date = data.get('published_date'),
                    authenticity   = prediction['prediction'],
                    confidence_score = prediction['confidence'],
                )
                saved += 1

            except Exception as exc:
                logger.warning(f"Could not save '{data.get('title','?')[:60]}': {exc}")
                errors += 1

        log.status           = 'success'
        log.articles_saved   = saved
        log.articles_skipped = skipped
        log.articles_errors  = errors
        log.finished_at      = timezone.now()
        log.save()
        logger.info(f"[auto_scrape_news] saved={saved} skipped={skipped} errors={errors}")
        return {'saved': saved, 'skipped': skipped, 'errors': errors}

    except Exception as exc:
        log.status      = 'failed'
        log.error_msg   = str(exc)
        log.finished_at = timezone.now()
        log.save()
        logger.error(f"[auto_scrape_news] fatal: {exc}")
        raise self.retry(exc=exc, countdown=300)   # retry after 5 min
