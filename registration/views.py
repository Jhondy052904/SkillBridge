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
from jobs.services.supabase_crud import get_jobs
from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import logout
import time

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['Location'] += '?t=' + str(int(time.time()))
    return response

# ============ LOGGING FOR AUDIT TRAIL ============
def log_action(action, entity, entity_id, request):
    try:
        supabase.table("audit_logs").insert({
            "entity": entity,
            "entity_id": entity_id,
            "action": action,
            "performed_by": request.session.get("user_email"),
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print("Audit log error:", e)

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

# def home(request):
#     """Resident dashboard view."""
#     # Restrict to residents only
#     if request.session.get('user_role') != 'Resident':
#         messages.error(request, "Access denied. Residents only.")
#         return redirect('login')

#     username = request.session.get("user_email")
#     verification_status = "No Profile"
#     user_profile = None
#     applied_jobs = []
#     registered_trainings = []
#     all_jobs = []
#     all_trainings = []
#     notifications = []  # renamed for consistency

#     if username:
#         # Fetch Django resident profile
#         resident = Resident.objects.filter(email=username).first()
#         if resident:
#             verification_status = resident.verification_status

#         # Fetch Supabase resident data
#         try:
#             res = supabase.table("resident").select("*").eq("email", username).single().execute()
#             user_profile = res.data if res.data else None
#         except Exception as e:
#             print("Supabase user profile fetch error:", e)

#         # Load applied jobs
#         applied_jobs = JobApplication.objects.filter(
#             resident__email=username
#         ).select_related("job")

#         # Load registered trainings
#         registered_trainings = Training.objects.filter(
#             trainingparticipation__resident__email=username
#         ).distinct()

#         # Fetch all active jobs
#         try:
#             all_jobs_data = get_jobs()
#             all_jobs = [job for job in all_jobs_data if job.get('Status') == 'Open']
#         except Exception as e:
#             messages.error(request, "Unable to load job listings.")
#             all_jobs = []

#         # Fetch all active trainings
#         try:
#             response = supabase.table("training").select("*").order("created_at", desc=True).execute()
#             all_trainings = response.data or []
#         except Exception as e:
#             messages.error(request, "Unable to load training events.")
#             all_trainings = []

#         # Fetch notifications
#         try:
#             notifications = get_all_notifications()
#         except Exception as e:
#             messages.error(request, "Unable to load notifications.")
#             notifications = []

#     return render(request, "registration/home.html", {
#         "verification_status": verification_status,
#         "user_profile": user_profile,
#         "applied_jobs": applied_jobs,
#         "registered_trainings": registered_trainings,
#         "all_jobs": all_jobs,
#         "all_trainings": all_trainings,
#         "notifications": notifications,
#     })

def home(request):
    """Resident dashboard view."""
    username = request.session.get("user_email")
    user_role = request.session.get("user_role")

    # Guest user: show public landing page
    if not username or user_role != "Resident":
        return render(request, "registration/index.html")  # public view

    # Resident dashboard logic
    verification_status = "No Profile"
    user_profile = None
    applied_jobs = []
    registered_trainings = []
    all_jobs = []
    all_trainings = []
    notifications = []

    # Fetch Django resident profile
    resident = Resident.objects.filter(email=username).first()
    if resident:
        verification_status = resident.verification_status

    # Fetch Supabase resident data
    try:
        res = supabase.table("resident").select("*").eq("email", username).single().execute()
        user_profile = res.data if res.data else None
    except Exception as e:
        print("Supabase user profile fetch error:", e)

    # Applied jobs
    applied_jobs = JobApplication.objects.filter(
        resident__email=username
    ).select_related("job")

    # Registered trainings
    registered_trainings = Training.objects.filter(
        trainingparticipation__resident__email=username
    ).distinct()

    # All jobs
    try:
        all_jobs_data = get_jobs()
        all_jobs = [job for job in all_jobs_data if job.get('Status') == 'Open']
    except Exception as e:
        messages.error(request, "Unable to load job listings.")
        all_jobs = []

    # All trainings
    try:
        response = supabase.table("training").select("*").order("created_at", desc=True).execute()
        all_trainings = response.data or []
    except Exception as e:
        messages.error(request, "Unable to load training events.")
        all_trainings = []

    # Notifications
    try:
        notifications = get_all_notifications()
    except Exception as e:
        messages.error(request, "Unable to load notifications.")
        notifications = []

    return render(request, "registration/home.html", {
        "verification_status": verification_status,
        "user_profile": user_profile,
        "applied_jobs": applied_jobs,
        "registered_trainings": registered_trainings,
        "all_jobs": all_jobs,
        "all_trainings": all_trainings,
        "notifications": notifications,
    })

def get_all_notifications():
    """Returns ALL visible notifications ordered from newest to oldest."""
    try:
        response = supabase.table("notifications") \
            .select("*") \
            .eq("visible", True) \
            .order("created_at", desc=True) \
            .execute()

        print("DEBUG NOTIFICATIONS:", response.data)
        return response.data or []

    except Exception as e:
        print("Notification fetch error:", e)
        return []

def forgot_password_view(request):
    return render(request, 'registration/forgot_password.html')


def community(request):
    return render(request, 'registration/community.html')


def aboutus(request):
    return render(request, 'registration/aboutus.html')


def jobhunt(request):
    return render(request, 'registration/jobhunt.html')

def supabase_reset_page(request):
    return render(request, "registration/reset_password.html")

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
    # Check login
    if not request.session.get('user_email'):
        messages.error(request, "You must log in first.")
        return redirect('login')

    # Restrict to officials only
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied.")
        return redirect('login')

    email = request.session.get("user_email")

    # Fetch official profile
    official_res = supabase.table("registration_official") \
        .select("*") \
        .ilike("email", email) \
        .single() \
        .execute()

    official = official_res.data
    official_id = str(official["id"]) if official else None

    # Fetch JOBS
    jobs = []
    try:
        jobs = supabase.table("jobs") \
            .select("*") \
            .eq("PostedBy", official_id) \
            .order("JobID", desc=True) \
            .execute().data
    except:
        messages.error(request, "Failed to load job posts")

    # Fetch TRAINING
    trainings = []
    try:
        trainings = supabase.table("training") \
            .select("*") \
            .eq("created_by", email) \
            .order("created_at", desc=True) \
            .execute().data
    except:
        messages.error(request, "Failed to load training data")

    # Fetch resident statistics
    total_residents = 0
    total_applicants = 0
    try:
        total_residents = supabase.table("resident").select("id", count="exact").execute().count
        total_applicants = supabase.table("JobApplication").select("ApplicationID", count="exact").execute().count
    except:
        pass  # ignore errors

    return render(request, "official/dashboard.html", {
        "official": official,
        "jobs": jobs,
        "trainings": trainings,
        "total_residents": total_residents,
        "total_applicants": total_applicants
    })



def post_job(request):
    """Official posts a job."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied: Officials only.")
        return redirect('home')

    try:
        email = request.user.email.strip().lower()
        official = supabase.table("registration_official").select("*").ilike("email", email).execute()

        if not official.data:
            official = supabase.table("registration_official").select("*").eq("user_id", request.user.id).execute()

        if not official.data:
            messages.error(request, "Official profile not found.")
            return redirect("official_dashboard")

        official_data = official.data[0]

        if request.method == 'POST':
            data = request.POST
            title = data['title']
            description = data['description']
            status = data.get('status', 'Open')

            result = supabase.table("jobs").insert({
                "Title": title,
                "Description": description,
                "PostedBy": str(official_data["id"]),
                "Status": status,
                "dateposted": datetime.utcnow().isoformat()  # FINAL + CORRECT
            }).execute()

            print("DEBUG INSERT RESULT:", result.data)

            job = result.data[0]
            job_id = job.get("JobID")

            log_action("create", "job", job_id, request)
            messages.success(request, "Job posted successfully!")
            return redirect("official_dashboard")

        return render(request, 'jobs/post_job.html')

    except Exception as e:
        print("EXCEPTION:", e)
        messages.error(request, f"Error posting job: {str(e)}")
        return redirect('official_dashboard')




def post_training(request):
    """Official posts a training."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied: Officials only.")
        return redirect('home')

    official_username = request.session.get("user_email")
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

        try:
            # Insert into Supabase to keep training IDs consistent (bigint)
            result = supabase.table("training").insert({
                "training_name": training_name,
                "description": description,
                "date_scheduled": date_scheduled,
                "location": location,
                "status": status,
                "created_by": request.session.get("user_email")
            }).execute()

            new_training = result.data[0] if result.data else None
            new_id = new_training.get("id") if new_training else None
            log_action("create", "training", new_id, request)

            messages.success(request, "Training posted successfully!")
            return redirect('official_dashboard')

        except Exception as e:
            messages.error(request, f"Error posting training: {e}")
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
# EDIT PROFILE VIEW
# ------------------------------------------------------------
from .forms import ResidentForm

@login_required
def edit_profile_view(request):
    email = request.session.get('user_email')
    if not email:
        return redirect('login')

    # Fetch current profile from Supabase
    try:
        res = supabase.table('resident').select('*').eq('email', email).single().execute()
        user_profile = res.data if res.data else {}
    except Exception as e:
        print("Supabase fetch error:", e)
        user_profile = {}

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        contact_number = request.POST.get('contact_number')
        employment_status = request.POST.get('employment_status')
        skills = request.POST.get('skills')

        # Update Supabase
        try:
            supabase.table('resident').update({
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'address': address,
                'contact_number': contact_number,
                'employment_status': employment_status,
                'skills': skills,
            }).eq('email', email).execute()
            messages.success(request, 'Profile updated successfully!')
            return redirect('edit_profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {e}')

    # Create form with initial data for choices
    form = ResidentForm(initial=user_profile)

    return render(request, 'registration/edit_profile.html', {
        'user_profile': user_profile,
        'form': form,
    })


# ------------------------------------------------------------
# VERIFICATION PANEL (UI Integrated)
# ------------------------------------------------------------

def pending_residents(request):
    """Displays all pending residents in the verification panel."""
    residents = Resident.objects.filter(verification_status="Pending")
    return render(request, "official/verification_panel.html", {"residents": residents})


def resident_details(request, resident_id):
    resp = supabase.table("resident").select("*").eq("id", resident_id).single().execute()
    resident = resp.data

    proof_url = None
    raw_proof = resident.get("proof_residency")

    if raw_proof:
        try:
            if raw_proof.startswith("\\x"):
                raw_proof = raw_proof[2:]  # remove \x
                proof_url = bytes.fromhex(raw_proof).decode()
        except Exception as e:
            print("URL Decode Error:", e)

    return render(request, "official/resident_details.html", {
        "resident": resident,
        "proof_url": proof_url
    })



from django.core.mail import send_mail
from django.conf import settings

def approve_resident(request, resident_id):
    try:
        response = supabase.table("resident").update({
            "verification_status": "verified"
        }).eq("id", resident_id).execute()

        # Send email
        try:
            resident_email = response.data[0]["email"]
            send_mail(
                subject="SkillBridge Account Approved",
                message=(
                    "Congratulations! Your SkillBridge account has been verified.\n"
                    "You can now log in and access job and training opportunities.\n\n"
                    "Thank you,\nSkillBridge Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[resident_email],
                fail_silently=False,
            )
            messages.success(request, "Resident approved and email sent!")
        except Exception:
            messages.warning(request, "Approved but email failed. Please notify manually.")

    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("verification_panel")


def deny_resident(request, resident_id):
    try:
        response = supabase.table("resident").update({
            "verification_status": "denied"
        }).eq("id", resident_id).execute()

        # Send rejection email
        try:
            resident_email = response.data[0]["email"]
            send_mail(
                subject="SkillBridge Account Verification Result",
                message=(
                    "Your SkillBridge registration was not approved.\n"
                    "Please contact your barangay office if you believe this is an error.\n\n"
                    "Thank you,\nSkillBridge Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[resident_email],
                fail_silently=False,
            )
            messages.success(request, "Resident denied and email sent.")
        except Exception:
            messages.warning(request, "Denied but email failed. Please notify manually.")

    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("verification_panel")


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

    def get_latest_notification():
        try:
            response = supabase.table("notifications") \
                .select("*") \
                .eq("visible", True) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print("Notification fetch error:", e)
            return None
