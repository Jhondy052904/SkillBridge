# from django.urls import path
# from . import views
# from django.contrib.auth import views as auth_views

# urlpatterns = [
#     path('', views.index, name='index'),
#     path('index/', views.index, name='index'),
#     path('signup/', views.signup, name='signup'),
#     path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
#     path('logout/', views.LogOut, name='logout'),
#     path('home/', views.home, name='home'),
    
    
# ]
from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('home/', views.home, name='home'),
    
    # Authentication URLs - using custom views
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('official/dashboard/', views.official_dashboard, name='official_dashboard'),
    path('official/post-job/', views.post_job, name='post_job'),
    path('official/post-training/', views.post_training, name='post_training'),
    path('official/post-event/', views.post_event, name='post_event'),
]