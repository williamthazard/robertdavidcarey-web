from django.urls import path
from . import views
from .feeds import LatestLogFeed

urlpatterns = [
    path('', views.home_view, name='home'),
    path('log/', views.log_index, name='log_index'),
    path('log/rss.xml', LatestLogFeed(), name='rss_feed'),
    path('log/<slug:entry_slug>/', views.log_detail, name='log_detail'),
    path('media/<path:path>', views.serve_media, name='serve_media'),
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('unsubscribe/<uuid:token>/', views.unsubscribe_view, name='unsubscribe'),
    path('<slug:page_slug>/', views.page_view, name='page_detail'),
]
