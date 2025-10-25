
from django.urls import path
from . import views

urlpatterns = [
    path('apply/<str:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('all/', views.list_all_applications, name='list_all_applications'),
    path('delete/<str:application_id>/', views.delete_application, name='delete_application'),
]