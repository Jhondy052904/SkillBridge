from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_listings, name='job_listings'),
    path('<str:job_id>/', views.job_detail, name='job_detail'),
    path('post/', views.post_job, name='post_job'),
    path('admin/post/', views.admin_post_job, name='admin_post_job'),
    path('list/', views.list_jobs, name='list_jobs'),
    path('update/<str:job_id>/', views.update_job_view, name='update_job'),
    path('delete/<str:job_id>/', views.delete_job_view, name='delete_job'),
]