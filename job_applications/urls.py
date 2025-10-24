from django.urls import path
from . import views

urlpatterns = [
    path('apply/<str:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('all/', views.list_all_applications, name='list_all_applications'),
    path('job/<str:job_id>/', views.job_applications, name='job_applications'),
    path('update/<str:application_id>/', views.update_application_status, name='update_application_status'),
    path('delete/<str:application_id>/', views.delete_application_view, name='delete_application'),
]