from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import NewsArticle, UserVerification
from .model_predictor import get_predictor
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Home page view"""
    context = {
        'page_title': 'Home - Fake News Detector'
    }
    return render(request, 'news/home.html', context)


def news_feed(request):
    """Display aggregated news from multiple sources"""
    # Get filter parameters
    category_filter = request.GET.get('category', 'all')
    source_filter = request.GET.get('source', 'all')
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'latest')

    # Query news articles
    articles = NewsArticle.objects.filter(is_active=True)

    # Apply search filter
    if search_query:
        from django.db.models import Q
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(source_name__icontains=search_query)
        )

    # Apply category filter
    if category_filter != 'all':
        articles = articles.filter(category=category_filter)

    # Apply source filter
    if source_filter != 'all':
        articles = articles.filter(source_name=source_filter)

    # Apply sorting
    if sort_by == 'latest':
        articles = articles.order_by('-scraped_date')
    elif sort_by == 'oldest':
        articles = articles.order_by('scraped_date')
    elif sort_by == 'confidence':
        articles = articles.order_by('-confidence_score')
    else:
        articles = articles.order_by('-scraped_date')  # Default

    # Get unique categories and sources for filters
    categories = NewsArticle.objects.values_list('category', flat=True).distinct()
    sources = NewsArticle.objects.values_list('source_name', flat=True).distinct()

    # Pagination
    paginator = Paginator(articles, 12)  # Show 12 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'News Feed',
        'page_obj': page_obj,
        'categories': categories,
        'sources': sources,
        'current_category': category_filter,
        'current_source': source_filter,
        'search_query': search_query,
        'current_sort': sort_by,
    }

    return render(request, 'news/news_feed.html', context)


def verify_news(request):
    """Manual news verification page"""
    result = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if content:
            try:
                # Get predictor and make prediction
                predictor = get_predictor()
                prediction = predictor.predict(content, title)

                # Save to database
                user_verification = UserVerification.objects.create(
                    title=title,
                    content=content,
                    result=prediction['prediction'],
                    confidence_score=prediction['confidence'],
                    ip_address=get_client_ip(request)
                )

                result = {
                    'prediction': prediction['prediction'],
                    'confidence': prediction['confidence'],
                    'confidence_percentage': prediction['confidence_percentage'],
                    'probability_fake': prediction['probability_fake'],
                    'probability_real': prediction['probability_real'],
                    'title': title if title else 'Untitled',
                }

                messages.success(request, 'News article verified successfully!')

            except Exception as e:
                logger.error(f"Error during prediction: {str(e)}")
                messages.error(request, 'An error occurred during verification. Please ensure the model is trained.')
        else:
            messages.warning(request, 'Please enter news content to verify.')

    context = {
        'page_title': 'Verify News',
        'result': result,
    }

    return render(request, 'news/verify_news.html', context)


def article_detail(request, pk):
    """View individual article with verification details"""
    try:
        article = NewsArticle.objects.get(pk=pk)

        context = {
            'page_title': article.title,
            'article': article,
        }

        return render(request, 'news/article_detail.html', context)

    except NewsArticle.DoesNotExist:
        messages.error(request, 'Article not found.')
        return redirect('news_feed')


def scrape_news(request):
    """Scrape News page — manual trigger dispatches a Celery task via AJAX."""
    return render(request, 'news/scrape_news.html', {'page_title': 'Scrape News'})


def statistics(request):
    """View statistics and analytics"""
    total_articles = NewsArticle.objects.count()
    real_articles = NewsArticle.objects.filter(authenticity='real').count()
    fake_articles = NewsArticle.objects.filter(authenticity='fake').count()
    unverified_articles = NewsArticle.objects.filter(authenticity='unverified').count()

    total_verifications = UserVerification.objects.count()
    user_fake_detections = UserVerification.objects.filter(result='fake').count()
    user_real_detections = UserVerification.objects.filter(result='real').count()

    # Category breakdown
    category_stats = {}
    for category, _ in NewsArticle.CATEGORY_CHOICES:
        count = NewsArticle.objects.filter(category=category).count()
        if count > 0:
            category_stats[category] = count

    context = {
        'page_title': 'Statistics',
        'total_articles': total_articles,
        'real_articles': real_articles,
        'fake_articles': fake_articles,
        'unverified_articles': unverified_articles,
        'total_verifications': total_verifications,
        'user_fake_detections': user_fake_detections,
        'user_real_detections': user_real_detections,
        'category_stats': category_stats,
    }

    return render(request, 'news/statistics.html', context)


def about(request):
    """About page"""
    context = {
        'page_title': 'About'
    }
    return render(request, 'news/about.html', context)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# API Views for AJAX requests
def api_verify_news(request):
    """API endpoint for news verification"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)

            title = data.get('title', '')
            content = data.get('content', '')

            if not content:
                return JsonResponse({'error': 'Content is required'}, status=400)

            predictor = get_predictor()
            prediction = predictor.predict(content, title)

            # Save verification
            UserVerification.objects.create(
                title=title,
                content=content,
                result=prediction['prediction'],
                confidence_score=prediction['confidence'],
                ip_address=get_client_ip(request)
            )

            return JsonResponse({
                'success': True,
                'prediction': prediction['prediction'],
                'confidence': prediction['confidence_percentage'],
                'details': prediction
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def trigger_scrape_task(request):
    """
    AJAX endpoint — scrape and verify articles immediately.
    Tries Celery first; if Redis is unavailable, runs synchronously in-process
    so it always works even without a running worker.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    # ── Try Celery async first ────────────────────────────────────────────
    try:
        from .tasks import auto_scrape_news
        task = auto_scrape_news.delay()
        return JsonResponse({'success': True, 'task_id': task.id, 'mode': 'celery'})
    except Exception:
        pass  # Redis not running — fall through to sync execution

    # ── Synchronous fallback ──────────────────────────────────────────────
    try:
        from django.utils import timezone
        from .models import NewsArticle, ScrapingLog
        from .news_scraper import NewsScraper
        from .model_predictor import get_predictor

        log = ScrapingLog.objects.create(status='running', triggered_by='manual')
        saved = skipped = errors = 0

        articles_raw = NewsScraper().get_sample_news()
        predictor    = get_predictor()

        for data in articles_raw:
            try:
                if NewsArticle.objects.filter(title=data['title']).exists():
                    skipped += 1
                    continue
                prediction = predictor.predict(data['content'], data['title'])
                NewsArticle.objects.create(
                    title            = data['title'],
                    content          = data['content'],
                    category         = data['category'],
                    source_name      = data['source_name'],
                    source_url       = data['source_url'],
                    published_date   = data.get('published_date'),
                    authenticity     = prediction['prediction'],
                    confidence_score = prediction['confidence'],
                )
                saved += 1
            except Exception as exc:
                logger.warning(f"Could not save article: {exc}")
                errors += 1

        log.status           = 'success'
        log.articles_saved   = saved
        log.articles_skipped = skipped
        log.articles_errors  = errors
        log.finished_at      = timezone.now()
        log.save()

        return JsonResponse({
            'success':  True,
            'task_id':  f'sync-{log.pk}',
            'mode':     'sync',
            'saved':    saved,
            'skipped':  skipped,
            'errors':   errors,
        })

    except Exception as exc:
        logger.error(f"Sync scrape failed: {exc}")
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


def scrape_status(request):
    """AJAX — return recent scraping log entries."""
    from .models import ScrapingLog
    logs = ScrapingLog.objects.all()[:10]
    data = []
    for log in logs:
        data.append({
            'id':        log.pk,
            'status':    log.status,
            'trigger':   log.get_triggered_by_display(),
            'started':   log.started_at.strftime('%Y-%m-%d %H:%M UTC'),
            'saved':     log.articles_saved,
            'skipped':   log.articles_skipped,
            'errors':    log.articles_errors,
            'duration':  log.duration_seconds,
        })
    return JsonResponse({'logs': data})


def model_performance(request):
    """Model performance charts page."""
    return render(request, 'news/model_performance.html', {'page_title': 'Model Performance'})
