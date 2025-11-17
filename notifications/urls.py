from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.latest_notification, name='latest_notification'),
]