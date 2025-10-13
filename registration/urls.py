from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('home/', views.home, name='home'),
    
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('official/dashboard/', views.official_dashboard, name='official_dashboard'),
    path('official/post-job/', views.post_job, name='post_job'),
    path('official/post-training/', views.post_training, name='post_training'),
    path('official/post-event/', views.post_event, name='post_event'),

    path('community/', views.community, name='community'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('jobhunt/', views.jobhunt, name='jobhunt'),
]