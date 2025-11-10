from django.urls import path
from . import views

urlpatterns = [
    path('post-job/', views.post_job, name='post_job'),
    path('list/', views.list_jobs, name='list_jobs'),
    path('update/<str:job_id>/', views.update_job_view, name='update_job'),
    path('delete/<str:job_id>/', views.delete_job_view, name='delete_job'),
    path('apply/<str:job_id>/', views.apply_job, name='apply_job'),
    path('success/', views.job_success, name='job_success'),
]
