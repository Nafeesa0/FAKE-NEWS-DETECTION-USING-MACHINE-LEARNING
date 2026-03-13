"""
URL Configuration for News App
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('news-feed/', views.news_feed, name='news_feed'),
    path('verify/', views.verify_news, name='verify_news'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('scrape/', views.scrape_news, name='scrape_news'),
    path('statistics/', views.statistics, name='statistics'),
    path('about/', views.about, name='about'),

    path('model/', views.model_performance, name='model_performance'),

    # API endpoints
    path('api/verify/', views.api_verify_news, name='api_verify_news'),

    # Celery task endpoints
    path('api/scrape/trigger/', views.trigger_scrape_task, name='trigger_scrape_task'),
    path('api/scrape/status/', views.scrape_status, name='scrape_status'),
]
