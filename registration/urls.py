from django.urls import path
from . import views

urlpatterns = [
    # -------- PUBLIC ROUTES --------
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('jobhunt/', views.jobhunt, name='jobhunt'),

    # -------- AUTH --------
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path("reset-password/", views.supabase_reset_page, name="supabase_reset"),

    # -------- OFFICIAL DASHBOARD --------
    path('official/dashboard/', views.official_dashboard, name='official_dashboard'),
    path('official/residents/', views.residents_list, name='residents_list'),
    path('official/post-job/', views.post_job, name='post_job'),
    path('official/post-training/', views.post_training, name='post_training'),
    path('official/post-event/', views.post_event, name='post_event'),
    path('official/verification-panel/', views.verification_panel, name='verification_panel'),
    path('verify/resident/<int:resident_id>/', views.resident_details, name='resident_details'),

    # -------- PROFILE --------
    path('profile/', views.edit_profile_view, name='edit_profile'),

    # -------- API --------
    path('api/registered_trainings/', views.api_registered_trainings, name='api_registered_trainings'),
    path('api/upload_certificate/', views.api_upload_certificate, name='api_upload_certificate'),
    path('api/delete_certificate/', views.api_delete_certificate, name='api_delete_certificate'),
    path('upload_certificate/', views.upload_certificate, name='upload_certificate'),

    # -------- VERIFICATION PANEL (UI) --------
    path('verify/pending/', views.pending_residents, name='pending_residents'),
    path('verify/resident/<int:resident_id>/', views.resident_details, name='resident_details'),
    path('verify/approve/<int:resident_id>/', views.approve_resident, name='approve_resident'),
    path('verify/deny/<int:resident_id>/', views.deny_resident, name='deny_resident'),
]
