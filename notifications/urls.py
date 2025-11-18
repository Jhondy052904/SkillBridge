from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.latest_notification, name='latest_notification'),
    path("clear/", views.clear_notifications, name="clear_notifications"),
]