from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import os
import time
from supabase import create_client
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Resident, Official, Job, Training, Event, JobApplication, TrainingParticipation

# ------------------------------------------------------------
# Supabase Setup
# ------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------------------
# Public Views
# ------------------------------------------------------------
def index(request):
    """Landing page."""
    return render(request, 'registration/index.html')



def home(request):
    """Resident dashboard."""
    username = request.session.get("user_email")
    verification_status = "No Profile"
    user_profile = None
    applied_jobs = []
    registered_trainings = []

    if username:
        # Fetch from Django Resident model for verification_status
        resident = Resident.objects.filter(email=username).first()
        if resident:
            verification_status = resident.verification_status

        # Fetch user_profile from Supabase
        try:
            res = supabase.table('resident').select('*').eq('email', username).single().execute()
            user_profile = res.data if res.data else None
        except Exception as e:
            print("Supabase fetch error in home:", e)
            user_profile = None

        # Fetch applied jobs
        applied_jobs = JobApplication.objects.filter(resident__email=username).select_related('job')

        # Fetch registered trainings
        registered_trainings = Training.objects.filter(trainingparticipation__resident__email=username).distinct()

    return render(request, 'registration/home.html', {
        "verification_status": verification_status,
        "user_profile": user_profile,
        "applied_jobs": applied_jobs,
        "registered_trainings": registered_trainings,
    })


def forgot_password_view(request):
    return render(request, 'registration/forgot_password.html')


def community(request):
    return render(request, 'registration/community.html')


def aboutus(request):
    return render(request, 'registration/aboutus.html')


def jobhunt(request):
    return render(request, 'registration/jobhunt.html')


# ------------------------------------------------------------
# SIGNUP — create new account in Supabase
# ------------------------------------------------------------
@csrf_protect
def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('username') 
        password = request.POST.get('password')
        role = request.POST.get('role', 'Resident')

        if not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'registration/signup.html')

        try:
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if hasattr(auth_response, "error") and auth_response.error:
                messages.error(request, "An account with this email already exists.")
                return render(request, 'registration/signup.html')

            supabase.table('resident').insert({
                "email": email,
                "verification_status": "Pending",
                "employment_status": "Unemployed",
            }).execute()

            send_mail(
                subject="SkillBridge Registration - Awaiting Approval",
                message=(
                    f"Hello!\n\n"
                    f"Thank you for signing up for SkillBridge.\n\n"
                    f"Please verify your email address using the confirmation link sent to your inbox.\n\n"
                    f"After verifying your email, your Barangay Official will review your registration.\n\n"
                    f"You’ll receive another message once your account has been approved.\n\n"
                    f"— The SkillBridge Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

            messages.success(request, "Signup successful! Please check your email to verify your account. Wait for official approval before logging in.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Signup failed: {e}")

    return render(request, 'registration/signup.html')

def confirm_email(request, email):
    """When resident clicks the email verification link."""
    try:
        response = supabase.table("resident").select("*").eq("email", email).single().execute()
        resident = response.data

        if not resident:
            return render(request, "registration/confirmation_error.html", {
                "message": "We could not find your registration record."
            })

        if resident["verification_status"].lower() != "verified":
            return render(request, "registration/confirmation_pending.html", {
                "message": (
                    "Your email has been verified successfully! 🎉 "
                    "However, your Barangay Official still needs to approve your account "
                    "before you can log in to SkillBridge. "
                    "Please wait for a confirmation email once your account is approved."
                )
            })

        from django.contrib.auth.models import User
        username = resident["email"]
        user, created = User.objects.get_or_create(username=username, email=username)
        if created:
            user.set_password("SkillBridge123") 
            user.save()

        return render(request, "registration/confirmation_success.html", {
            "message": "Your account has been verified and approved! You may now log in."
        })

    except Exception as e:
        return render(request, "registration/confirmation_error.html", {
            "message": f"An error occurred: {e}"
        })

# ------------------------------------------------------------
# LOGIN 
# ------------------------------------------------------------
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.shortcuts import render, redirect
from skillbridge.supabase_client import supabase


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Authenticate with Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = auth_response.user
            if not user:
                messages.error(request, "Invalid email or password.")
                return render(request, 'registration/login.html')

            # ✅ Check if email belongs to an official
            OFFICIAL_EMAILS = ["official@skillbridge.com", "admin@skillbridge.com"]

            if email in OFFICIAL_EMAILS:
                messages.success(request, "Welcome, Barangay Official!")
                request.session['user_email'] = email
                request.session['user_role'] = 'Official'

                # 👇 Make Django recognize this user as authenticated
                django_user, _ = User.objects.get_or_create(username=email, defaults={'email': email, 'is_staff': True})
                login(request, django_user, backend='django.contrib.auth.backends.ModelBackend')

                return redirect('official_dashboard')

            # ✅ Otherwise, check resident status
            resident_data = supabase.table('resident').select('*').eq('email', user.email).execute()

            if resident_data.data:
                resident = resident_data.data[0]
                status = resident.get('verification_status', '').lower()

                if status == 'verified':
                    request.session['user_email'] = user.email
                    request.session['user_role'] = 'Resident'
                    messages.success(request, "Welcome back!")

                    # 👇 Make Django recognize the resident as logged in
                    django_user, _ = User.objects.get_or_create(username=user.email, defaults={'email': user.email})
                    login(request, django_user, backend='django.contrib.auth.backends.ModelBackend')

                    return redirect('home')

                else:
                    messages.warning(request, "Your account is still pending approval.")
                    return redirect('login')

            messages.error(request, "No matching account found.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Login failed: {str(e)}")

    # Ensure session is saved to set CSRF token cookie
    request.session['login_page_loaded'] = True
    return render(request, 'registration/login.html')





# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    response = redirect('login')
    # Prevent caching to ensure fresh CSRF token on login page
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    # Add timestamp to URL to force fresh load
    response['Location'] += '?t=' + str(int(time.time()))
    return response


# ------------------------------------------------------------
# OFFICIAL DASHBOARD & POSTING
# ------------------------------------------------------------

def official_dashboard(request):
    # ✅ Check if logged in via email (new method)
    if not request.session.get('user_email'):
        messages.error(request, "You must log in first.")
        return redirect('login')

    # ✅ Ensure only Officials can access
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied: Officials only.")
        return redirect('home')

    # You can safely load data here
    official_email = request.session.get("user_email")

    return render(request, 'official/dashboard.html', {
        "official_email": official_email
    })




def post_job(request):
    """Official posts a job."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied: Officials only.")
        return redirect('home')

    official_username = request.session.get("username")
    official = Official.objects.filter(user__username=official_username).first()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        status = request.POST.get('status', 'Open')

        if not official:
            messages.error(request, "Official profile not found.")
            return redirect('official_dashboard')

        Job.objects.create(
            title=title,
            description=description,
            requirements=requirements,
            posted_by=official,
            status=status
        )
        messages.success(request, "Job posted successfully!")
        return redirect('official_dashboard')

    return render(request, 'jobs/post_job.html')




def post_training(request):
    """Official posts a training."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied: Officials only.")
        return redirect('home')

    official_username = request.session.get("username")
    official = Official.objects.filter(user__username=official_username).first()

    if request.method == 'POST':
        training_name = request.POST.get('training_name')
        description = request.POST.get('description')
        date_scheduled = request.POST.get('date_scheduled')
        location = request.POST.get('location')
        status = request.POST.get('status', 'Upcoming')

        if not official:
            messages.error(request, "Official profile not found.")
            return redirect('official_dashboard')

        Training.objects.create(
            training_name=training_name,
            description=description,
            organizer=official,
            date_scheduled=date_scheduled,
            location=location,
            status=status
        )
        messages.success(request, "Training posted successfully!")
        return redirect('official_dashboard')

    return render(request, 'official/post_training.html')



def post_event(request):
    """Official posts an event."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied: Officials only.")
        return redirect('home')

    official_username = request.session.get("username")
    official = Official.objects.filter(user__username=official_username).first()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_event = request.POST.get('date_event')
        location = request.POST.get('location')
        status = request.POST.get('status', 'Upcoming')

        if not official:
            messages.error(request, "Official profile not found.")
            return redirect('official_dashboard')

        Event.objects.create(
            title=title,
            description=description,
            date_event=date_event,
            location=location,
            posted_by=official,
            status=status
        )
        messages.success(request, "Event posted successfully!")
        return redirect('official_dashboard')

    return render(request, 'official/post_event.html')


# ------------------------------------------------------------
# PROFILE VIEW (from Supabase)
# ------------------------------------------------------------

def profile_view(request):
    email = request.session.get('user_email')
    if not email:
        return redirect('login')

    try:
        res = supabase.table('resident').select('*').eq('email', email).single().execute()
        user_profile = res.data if res.data else None
    except Exception as e:
        print("Supabase fetch error:", e)
        user_profile = None

    return render(request, 'registration/edit_profile.html', {'user_profile': user_profile})


# ------------------------------------------------------------
# VERIFICATION PANEL (UI Integrated)
# ------------------------------------------------------------

def pending_residents(request):
    """Displays all pending residents in the verification panel."""
    residents = Resident.objects.filter(verification_status="Pending")
    return render(request, "official/verification_panel.html", {"residents": residents})



def resident_details(request, resident_id):
    """Fetch resident details from Supabase 'resident' table."""
    try:
        # Fetch single record from Supabase
        response = supabase.table("resident").select("*").eq("id", resident_id).single().execute()

        if not response.data:
            messages.error(request, "Resident not found in Supabase.")
            return redirect('verification_panel')

        resident = response.data

        return render(request, "official/resident_details.html", {"resident": resident})

    except Exception as e:
        messages.error(request, f"Error retrieving resident details: {e}")
        return redirect('verification_panel')




def approve_resident(request, resident_id):
    try:
        #update Supabase resident table
        update_response = supabase.table("resident").update({
            "verification_status": "verified"
        }).eq("id", resident_id).execute()

        if not update_response.data:
            return JsonResponse({
                "success": False,
                "message": f"Resident with ID {resident_id} not found in Supabase."
            }, status=404)

        #Get resident email for notification
        resident = update_response.data[0]
        email = resident.get("email")

        #Send approval email
        if email:
            try:
                send_mail(
                    subject="SkillBridge Account Verified",
                    message=(
                        "Your SkillBridge account has been approved by your Barangay Official.\n\n"
                        "You can now log in to the SkillBridge platform using your registered email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception as e:
                print("Email sending failed:", e)

        #Return success response
        return JsonResponse({
            "success": True,
            "message": f"Resident ID {resident_id} approved successfully."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


def deny_resident(request, resident_id):
    try:
        # Update Supabase
        update_response = supabase.table("resident").update({
            "verification_status": "rejected"
        }).eq("id", resident_id).execute()

        if not update_response.data:
            return JsonResponse({
                "success": False,
                "message": f"Resident with ID {resident_id} not found in Supabase."
            }, status=404)

        resident = update_response.data[0]
        email = resident.get("email")

        if email:
            try:
                send_mail(
                    subject="SkillBridge Account Rejected",
                    message=(
                        "Your SkillBridge account verification was not approved.\n\n"
                        "Please contact your Barangay Office for more information."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception as e:
                print("Email sending failed:", e)

        return JsonResponse({
            "success": True,
            "message": f"Resident ID {resident_id} denied successfully."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


def verification_panel(request):
    """Official Verification Panel using Supabase 'resident' table."""
    if request.session.get("user_role") != "Official":
        messages.error(request, "Access denied. Officials only.")
        return redirect('home')

    try:
        response = supabase.table("resident").select("*").eq("verification_status", "pending").execute()
        residents = response.data or []

    except Exception as e:
        residents = []
        messages.error(request, f"Unable to retrieve pending accounts: {e}")

    return render(request, "official/verification_panel.html", {"residents": residents})
