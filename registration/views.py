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
from .models import Resident, Official, Job, Training, Event, JobApplication, TrainingParticipation, Skill
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
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# Create both an anon client (for public reads) and a service-role client (for privileged writes)
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY or SUPABASE_KEY)
supabase_service = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        current_status = resident.current_status
    else:
        current_status = 'Not Hired'

    # Fetch Supabase resident data
    try:
        res = supabase_service.table("resident").select("*").eq("email", username).single().execute()
        user_profile = res.data if res.data else None
    except Exception as e:
        print("Supabase user profile fetch error:", e)

    # Applied jobs: removed backend fetch to speed up dashboard (UI removed)
    applied_jobs = []

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

    # Certificates
    certificates = []
    try:
        if user_profile:
            response = supabase.table("training_certificates").select("*").eq("resident_id", user_profile['id']).order("uploaded_at", desc=True).execute()
            certificates = response.data or []
            # Fetch training names for each certificate
            for cert in certificates:
                try:
                    training_resp = supabase.table("training").select("training_name").eq("id", cert['training_id']).single().execute()
                    cert['training_name'] = training_resp.data['training_name'] if training_resp.data else 'Unknown Training'
                except Exception as e:
                    cert['training_name'] = 'Unknown Training'
    except Exception as e:
        print("Certificates fetch error:", e)
        certificates = []

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
        "current_status": current_status,
        "certificates": certificates,
    })


def api_registered_trainings(request):
    """Returns JSON list of trainings the logged-in resident registered for, including attendance_status."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    email = request.session.get('user_email') or request.user.email
    try:
        resp = supabase.table("training_attendees").select("*").eq("email", email).execute()
        attendees = resp.data or []
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    results = []
    for a in attendees:
        training = None
        try:
            tresp = supabase.table("training").select("*").eq("id", a.get("training_id")).single().execute()
            training = tresp.data
        except Exception:
            training = None

        results.append({
            "training_id": a.get("training_id"),
            "training_name": training.get("training_name") if training else None,
            "date_scheduled": training.get("date_scheduled") if training else None,
            "attendance_status": a.get("attendance_status"),
        })

    return JsonResponse(results, safe=False)

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


@login_required
def api_upload_certificate(request):
    """API endpoint for residents to upload training certificates.

    Expects multipart/form-data POST with fields:
      - training_id
      - certificates (one or many files)

    Uploads files to `training_certificates` bucket and inserts a row into
    the `training_certificates` table with integer `resident_id` and
    `training_id` and `uploaded_at` timestamp.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    email = request.session.get('user_email')
    if not email:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Use Supabase Resident UUID for resident_id
    try:
        res = supabase_service.table("resident").select("id").eq("email", email).single().execute()
        resident_id = res.data['id']
    except Exception:
        return JsonResponse({"error": "Resident profile not found"}, status=404)

    training_id = request.POST.get('training_id')
    if not training_id:
        return JsonResponse({"error": "training_id is required"}, status=400)
    try:
        training_id_int = int(training_id)
    except Exception:
        return JsonResponse({"error": "training_id must be an integer"}, status=400)

    # Verify resident is registered for this training
    try:
        att_resp = supabase.table("training_attendees").select("*").eq("email", email).eq("training_id", training_id_int).single().execute()
        registered = bool(att_resp.data)
    except Exception:
        registered = False

    if not registered:
        try:
            all_att = supabase.table("training_attendees").select("*").eq("email", email).execute()
            attendees = all_att.data or []
            registered = any(str(a.get("training_id")) == str(training_id_int) for a in attendees)
        except Exception:
            registered = False

    if not registered:
        return JsonResponse({"error": "Not registered for this training"}, status=403)

    files = request.FILES.getlist('certificates')
    if not files:
        return JsonResponse({"error": "No files uploaded"}, status=400)

    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    uploaded = []
    errors = []
    bucket = os.getenv('SUPABASE_CERT_BUCKET', 'training_certificates')

    for f in files:
        if f.content_type not in allowed_types:
            errors.append(f"File {f.name}: unsupported type {f.content_type}")
            continue

        # create safe path
        import re
        clean_name = re.sub(r'[^\w\.-]', '_', f.name)  # replace non-word, non-dot, non-dash with _
        timestamp = int(time.time())
        file_path = f"{resident_id}/{training_id_int}/{timestamp}_{clean_name}"

        try:
            supabase_service.storage.from_(bucket).upload(file_path, f.read(), {"content-type": f.content_type})
            public_url = supabase_service.storage.from_(bucket).get_public_url(file_path)
        except Exception as e:
            errors.append(f"Storage upload error for {f.name}: {repr(e)}")
            continue

        cert_row = {
            "resident_id": resident_id,
            "training_id": training_id_int,
            "file_name": f.name,
            "file_type": f.content_type.split('/')[-1],
            "certificate_url": public_url,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        try:
            supabase_service.table("training_certificates").insert(cert_row).execute()
            uploaded.append({"file_name": f.name, "url": public_url})
        except Exception as e:
            errors.append(f"DB insert error for {f.name}: {repr(e)}")
            continue

    if not uploaded:
        return JsonResponse({"error": "No files were uploaded successfully", "details": errors}, status=400)

    return JsonResponse({"uploaded": uploaded})

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
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'Resident')

        if not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'registration/signup.html')

        # Get form data
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        contact_number = request.POST.get('contact')
        barangay = request.POST.get('barangay')
        sublocation = request.POST.get('sublocation')
        house_number = request.POST.get('house_number')
        skills = request.POST.get('skills')
        # For address, combine barangay, sublocation, house_number
        address = f"{house_number}, {sublocation}, {barangay}"

        # Handle proof of residency file
        proof_data = None
        proof_file = request.FILES.get('proof_residency')
        if proof_file:
            bucket = 'proof_residency'  # Assume bucket exists for proof files
            file_path = f"{email}/{proof_file.name}"
            supabase_service.storage.from_(bucket).upload(file_path, proof_file.read(), {"content-type": proof_file.content_type})
            public_url = supabase_service.storage.from_(bucket).get_public_url(file_path)
            proof_data = public_url.encode('utf-8')

        try:
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if auth_response.user is None:
                messages.error(request, "Signup failed. Please check your email format and password requirements.")
                return render(request, 'registration/signup.html')

            # Create Django User
            from django.contrib.auth.models import User
            django_user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email}
            )
            if created:
                django_user.set_password(password)  # Set the password
                django_user.save()

            # Auth succeeded, now insert resident record
            supabase.table('resident').insert({
                "user_id": django_user.id,
                "email": email,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "contact_number": contact_number,
                "address": address,
                "skills": skills,
                "proof_residency": proof_data,
                "verification_status": "Pending Verification",
                "employment_status": "Unemployed",
            }).execute()

            # Send verification email
            try:
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
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email sending failed: {e}")
                messages.warning(request, "Signup successful, but there was an issue sending the verification email. Please contact support if you don't receive it.")

            messages.success(request, "Signup successful! Please check your email to verify your account. Wait for official approval before logging in.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Signup failed: {e}")

    return render(request, 'registration/signup.html')

def confirm_email(request, email):
    """When resident clicks the email verification link."""
    try:
        response = supabase_service.table("resident").select("*").eq("email", email).single().execute()
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
                request.session.save()
        
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
                    request.session.save()
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
        total_residents = supabase_service.table("resident").select("id", count="exact").execute().count
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


def residents_list(request):
    """Official Residents List Page."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied.")
        return redirect('login')

    if request.method == 'POST':
        resident_id = request.POST.get('resident_id')
        if resident_id:
            try:
                supabase.table("resident").update({"verification_status": "deactivated"}).eq("id", resident_id).execute()
                messages.success(request, "Resident account deactivated.")
                log_action("deactivate", "resident", resident_id, request)
            except Exception as e:
                messages.error(request, f"Error deactivating resident: {e}")
        return redirect('residents_list')

    search_query = request.GET.get('search', '').strip()

    try:
        query = supabase_service.table("resident").select("*").neq("verification_status", "deactivated")
        if search_query:
            query = query.or_(f"first_name.ilike.%{search_query}%,last_name.ilike.%{search_query}%")
        response = query.execute()
        residents = response.data or []
    except Exception as e:
        residents = []
        messages.error(request, f"Unable to load residents: {e}")

    # Fetch current_status from Django Resident
    for resident in residents:
        email = resident.get('email')
        django_resident = Resident.objects.filter(email=email).first()
        if django_resident:
            resident['current_status'] = django_resident.current_status
        else:
            resident['current_status'] = 'Not Hired'

    # Fetch official profile for sidebar
    email = request.session.get("user_email")
    official_res = supabase.table("registration_official") \
        .select("*") \
        .ilike("email", email) \
        .single() \
        .execute()
    official = official_res.data

    return render(request, "official/residents_list.html", {"residents": residents, "official": official, "request": request})


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
        res = supabase_service.table('resident').select('*').eq('email', email).single().execute()
        user_profile = res.data if res.data else {}
    except Exception as e:
        print("Supabase fetch error:", e)
        user_profile = {}

    # Fetch current_status from Django Resident
    resident = Resident.objects.filter(email=email).first()
    if resident:
        user_profile['current_status'] = resident.current_status

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        contact_number = request.POST.get('contact_number')
        employment_status = request.POST.get('employment_status')
        # With multi-select, getlist returns list of selected skill ids (as strings)
        skills_selected = request.POST.getlist('skills')
        # We'll store a legacy CSV string in Supabase's `skills` text field for compatibility
        skills_csv = ''
        if skills_selected:
            from .models import Skill
            # Map selected skill ids to skill names where possible
            try:
                skill_qs = Skill.objects.filter(id__in=skills_selected)
                skill_names = [s.skill_name for s in skill_qs]
                skills_csv = ','.join(skill_names)
            except Exception:
                # Fallback: join raw posted values
                skills_csv = ','.join(skills_selected)
        current_status = request.POST.get('current_status')

        # Update Supabase
        try:
            supabase_service.table('resident').update({
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'address': address,
                'contact_number': contact_number,
                'employment_status': employment_status,
                'skills': skills_csv,
                'status': current_status,
            }).eq('email', email).execute()

            # Update Django Resident
            resident, created = Resident.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'middle_name': middle_name,
                    'address': address,
                    'contact_number': contact_number,
                    'employment_status': employment_status,
                    'current_status': current_status,
                }
            )
            if not created:
                resident.first_name = first_name
                resident.last_name = last_name
                resident.middle_name = middle_name
                resident.address = address
                resident.contact_number = contact_number
                resident.employment_status = employment_status
                resident.current_status = current_status
                resident.save()

            # Sync skills selection via SupabaseResident-backed resident_skills
            try:
                if skills_selected:
                    skill_objs = Skill.objects.filter(id__in=skills_selected)
                    # Use Resident helper to set skills (writes to resident_skills)
                    resident.set_skills(skill_objs)
                else:
                    resident.set_skills([])
            except Exception as e:
                # Log but don't block profile save
                print('Error syncing resident skills:', e)

            messages.success(request, 'Profile updated successfully!')
            return redirect('edit_profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {e}')

    # Create form with initial data for choices
    initial = user_profile.copy() if isinstance(user_profile, dict) else {}
    # If we have a Django Resident, use its skills M2M for initial selection
    try:
        from .models import Skill
        if resident:
            initial['skills'] = list(resident.get_skills().values_list('id', flat=True))
        else:
            # Try to parse comma-separated skills from Supabase profile
            supa_skills = user_profile.get('skills') if isinstance(user_profile, dict) else None
            if supa_skills:
                # map names to ids where possible
                names = [s.strip() for s in supa_skills.split(',') if s.strip()]
                skill_qs = Skill.objects.filter(skill_name__in=names)
                initial['skills'] = list(skill_qs.values_list('id', flat=True))
    except Exception:
        # If mapping fails, leave skills initial blank
        pass

    form = ResidentForm(initial=initial)

    return render(request, 'registration/edit_profile.html', {
        'user_profile': user_profile,
        'form': form,
        'all_skills': Skill.objects.all() if 'Skill' in globals() or 'Skill' in locals() else [],
    })


# ------------------------------------------------------------
# VERIFICATION PANEL (UI Integrated)
# ------------------------------------------------------------

def pending_residents(request):
    """Displays all pending residents in the verification panel."""
    residents = Resident.objects.filter(verification_status="Pending")
    return render(request, "official/verification_panel.html", {"residents": residents})


def resident_details(request, resident_id):
    resp = supabase_service.table("resident").select("*").eq("id", resident_id).single().execute()
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


def dashboard_resident_details(request, resident_id):
    """Dashboard Resident Details Page."""
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied.")
        return redirect('login')

    # Fetch resident from Supabase
    try:
        resp = supabase_service.table("resident").select("*").eq("id", resident_id).single().execute()
        resident = resp.data
    except Exception as e:
        messages.error(request, f"Resident not found: {e}")
        return redirect('residents_list')

    # Fetch current_status from Django Resident
    django_resident = Resident.objects.filter(email=resident['email']).first()
    current_status = django_resident.current_status if django_resident else 'Not Hired'

    # Fetch attended trainings
    attended_trainings = []
    try:
        attendees_resp = supabase.table("training_attendees").select("*").eq("email", resident['email']).in_("attendance_status", ["Attended", "Completed"]).execute()
        attendees = attendees_resp.data or []
        for att in attendees:
            try:
                training_resp = supabase.table("training").select("training_name, date_scheduled").eq("id", att['training_id']).single().execute()
                training = training_resp.data
                if training:
                    attended_trainings.append({
                        'name': training['training_name'],
                        'date': training['date_scheduled']
                    })
            except Exception as e:
                print(f"Training fetch error for {att['training_id']}: {e}")
    except Exception as e:
        print(f"Attended trainings fetch error: {e}")

    # Fetch skills
    skills = []
    try:
        skills_resp = supabase.table("resident_skills").select("skill_id").eq("resident_id", resident_id).execute()
        skill_ids = [s['skill_id'] for s in skills_resp.data or []]
        if skill_ids:
            skills_resp = supabase.table("skill_list").select("SkillName").in_("SkillID", skill_ids).execute()
            skills = [s['SkillName'] for s in skills_resp.data or []]
    except Exception as e:
        print(f"Skills fetch error: {e}")

    return render(request, "official/dashboard_resident_details.html", {
        "resident": resident,
        "current_status": current_status,
        "attended_trainings": attended_trainings,
        "skills": skills
    })



from django.core.mail import send_mail
from django.conf import settings

def approve_resident(request, resident_id):
    try:
        response = supabase_service.table("resident").update({
            "verification_status": "Verified"
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
        response = supabase_service.table("resident").update({
            "verification_status": "Rejected"
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
        response = supabase_service.table("resident").select("*").eq("verification_status", "Pending Verification").execute()
        residents = response.data or []

    except Exception as e:
        residents = []
        messages.error(request, f"Unable to retrieve pending accounts: {e}")

    return render(request, "official/verification_panel.html", {"residents": residents})

@login_required
def api_delete_certificate(request):
    """API endpoint for residents to delete training certificates."""
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    email = request.session.get('user_email')
    if not email:
        return JsonResponse({"error": "Authentication required"}, status=401)

    cert_id = request.POST.get('cert_id')
    if not cert_id:
        return JsonResponse({"error": "cert_id is required"}, status=400)

    try:
        cert_id_int = int(cert_id)
    except Exception:
        return JsonResponse({"error": "cert_id must be an integer"}, status=400)

    # Fetch certificate to verify ownership
    try:
        cert_resp = supabase.table("training_certificates").select("*").eq("id", cert_id_int).single().execute()
        cert = cert_resp.data
        if not cert:
            return JsonResponse({"error": "Certificate not found"}, status=404)

        # Check if resident owns this certificate
        if cert['resident_id'] != supabase_service.table("resident").select("id").eq("email", email).single().execute().data['id']:
            return JsonResponse({"error": "Not authorized"}, status=403)

    except Exception as e:
        return JsonResponse({"error": f"Verification error: {str(e)}"}, status=500)

    # Delete from storage
    bucket = os.getenv('SUPABASE_CERT_BUCKET', 'training_certificates')
    file_path = cert['certificate_url'].split('/')[-1]  # Assuming URL ends with path
    # Actually, need to extract path from URL
    # For simplicity, assume path is known or parse
    # But to make it work, perhaps store file_path in DB
    # For now, try to delete assuming path is resident_id/training_id/filename
    try:
        # Extract file path from certificate_url
        # Assuming URL is like https://.../bucket/resident_id/training_id/filename
        url_parts = cert['certificate_url'].split('/')
        file_path = '/'.join(url_parts[-3:])  # last 3 parts
        supabase_service.storage.from_(bucket).remove([file_path])
    except Exception as e:
        print("Storage delete error:", e)
        # Continue to delete DB record

    # Delete from DB
    try:
        supabase_service.table("training_certificates").delete().eq("id", cert_id_int).execute()
    except Exception as e:
        return JsonResponse({"error": f"DB delete error: {str(e)}"}, status=500)

    return JsonResponse({"success": True})

@login_required
def upload_certificate(request):
    """Upload certificate for resident."""
    if request.method == 'POST':
        email = request.session.get('user_email')
        if not email:
            return JsonResponse({"error": "Not authenticated"}, status=401)

        certificate_name = request.POST.get('certificate_name')
        certificate_file = request.FILES.get('certificate_file')

        if not certificate_name or not certificate_file:
            return JsonResponse({"error": "Missing fields"}, status=400)

        try:
            # Upload file to Supabase Storage (use training_certificates bucket)
            bucket = os.getenv('SUPABASE_CERT_BUCKET', 'training_certificates')
            file_path = f"{email}/{certificate_file.name}"
            supabase_service.storage.from_(bucket).upload(file_path, certificate_file.read(), {'content-type': certificate_file.content_type})

            # Get public URL
            public_url = supabase_service.storage.from_(bucket).get_public_url(file_path)

            # Insert into resident_certificates table (legacy table) - keep existing behavior
            supabase_service.table("resident_certificates").insert({
                "resident_email": email,
                "certificate_name": certificate_name,
                "file_url": public_url,
                "upload_date": datetime.utcnow().isoformat()
            }).execute()

            return JsonResponse({"success": True})

        except Exception as e:
            print("Upload error:", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)
    # -- put near other views in registration/views.py --

from django.http import JsonResponse
from django.utils.dateparse import parse_datetime

def calendar_view(request):
    """
    Renders calendar page for residents.
    The page loads events from /calendar/events/ via AJAX.
    """
    # Protect: only residents should see dashboard calendar; but public view permitted.
    username = request.session.get("user_email")
    user_role = request.session.get("user_role")
    # If you want to restrict strictly to logged-in residents:
    # if not username or user_role != "Resident": return redirect('login')

    # Pass small context (title etc.) and let frontend fetch events
    return render(request, "registration/calendar.html", {
        "page_title": "Calendar | SkillBridge",
    })


def calendar_events_api(request):
    """
    Returns JSON list of events (jobs + trainings) expected by FullCalendar.
    Only returns ongoing events:
      - training: exclude status == "Completed" or "Closed"
      - jobs: include jobs with Status == "Open"
    """
    events = []
    try:
        # Trainings: use date_scheduled as event start
        trainings_resp = supabase.table("training").select("*").execute()
        trainings = trainings_resp.data or []
        for t in trainings:
            status = (t.get("status") or "").lower()
            if status in ("completed", "closed"):
                continue
            title = t.get("training_name") or "Training"
            date = t.get("date_scheduled") or t.get("created_at")
            # ensure date format acceptable to FullCalendar (ISO or YYYY-MM-DD)
            if date:
                events.append({
                    "id": f"training-{t.get('id')}",
                    "title": f"[Training] {title}",
                    "start": date,
                    "allDay": True,
                    "extendedProps": {
                        "type": "training",
                        "raw": t,
                    }
                })

        # Jobs: use dateposted (or created_at) and require Status == "Open"
        jobs_resp = supabase.table("jobs").select("*").execute()
        jobs = jobs_resp.data or []
        for j in jobs:
            status = (j.get("Status") or "").lower()
            if status != "open":
                continue
            title = j.get("Title") or "Job"
            date = j.get("dateposted") or j.get("created_at")
            if date:
                events.append({
                    "id": f"job-{j.get('JobID') or j.get('id')}",
                    "title": f"[Job] {title}",
                    "start": date,
                    "allDay": True,
                    "extendedProps": {
                        "type": "job",
                        "raw": j,
                    }
                })
    except Exception as e:
        # return an error object that frontend can detect
        return JsonResponse({"error": f"Unable to load events: {e}"}, status=500)

    return JsonResponse(events, safe=False)

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
