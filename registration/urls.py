from django.urls import path
from . import views

urlpatterns = [
    # -------- PUBLIC ROUTES --------
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('community/', views.community, name='community'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('jobhunt/', views.jobhunt, name='jobhunt'),

    # -------- AUTH --------
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),

    # -------- OFFICIAL DASHBOARD --------
    path('official/dashboard/', views.official_dashboard, name='official_dashboard'),
    path('official/post-job/', views.post_job, name='post_job'),
    path('official/post-training/', views.post_training, name='post_training'),
    path('official/post-event/', views.post_event, name='post_event'),
    path('official/verification-panel/', views.verification_panel, name='verification_panel'),
    path('verify/resident/<int:resident_id>/', views.resident_details, name='resident_details'),



    # -------- PROFILE --------
    path('profile/', views.edit_profile_view, name='edit_profile'),

    # -------- VERIFICATION PANEL (UI) --------
    path('verify/pending/', views.pending_residents, name='pending_residents'),
    path('verify/resident/<int:resident_id>/', views.resident_details, name='resident_details'),
    path('verify/approve/<int:resident_id>/', views.approve_resident, name='approve_resident'),
    path('verify/deny/<int:resident_id>/', views.deny_resident, name='deny_resident'),
]