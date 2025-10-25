from django.urls import path
from . import views

urlpatterns = [
    path('post/', views.post_skill, name='post_skill'),
    path('admin/post/', views.admin_post_skill, name='admin_post_skill'),
    path('list/', views.list_skills, name='list_skills'),
    path('update/<str:skill_id>/', views.update_skill_view, name='update_skill'),
    path('delete/<str:skill_id>/', views.delete_skill_view, name='delete_skill'),
]