from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

from .models import Job, Training, Official, Event, Resident
from django.contrib.auth.decorators import login_required

from .models import UserAccount

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from registration.models import UserAccount, Resident, JobApplication, TrainingParticipation

from django.shortcuts import render, get_object_or_404
from .models import Resident, ResidentSkill

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ResidentForm

def user_profile(request):
    user = request.user
    user_profile = get_object_or_404(Resident, user__username=user.username)
    skills = ResidentSkill.objects.filter(resident=user_profile).select_related('skill')

    context = {
        'user_profile': user_profile,
        'skills': skills,
        'user': user,
    }
    return render(request, 'registration/profile.html', context)

# -----------------------------
# Public Views
# -----------------------------

def index(request):
    return render(request, 'registration/index.html')

def forgot_password_view(request):
    return render(request, 'registration/forgot_password.html')

def signup_view(request):
    return render(request, 'registration/signup.html')

def community(request):
    return render(request, 'registration/community.html')

def aboutus(request):
    return render(request, 'registration/aboutus.html')

def jobhunt(request):
    return render(request, 'registration/jobhunt.html')


@login_required(login_url='login')
def home(request):
    verification_status = None
    applied_jobs = []
    registered_trainings = []
    resident = None

    # --- Get Resident linked to logged-in user ---
    try:
        user_account = UserAccount.objects.get(username=request.user.username)
        resident = Resident.objects.get(user=user_account)
        verification_status = resident.verification_status
        user_profile = resident
    except (UserAccount.DoesNotExist, Resident.DoesNotExist):
        verification_status = "No Profile"
        resident = None

    # --- Fetch Applied Jobs ---
    if resident:
        applied_jobs = JobApplication.objects.filter(resident=resident).select_related('job').order_by('-date_applied')
        print("✅ Applied jobs:", applied_jobs)

    # --- Fetch Trainings ---
    if resident:
        registered_trainings = TrainingParticipation.objects.filter(resident=resident).select_related('training').order_by('-date_registered')
        print("✅ Trainings:", registered_trainings)

    # --- Render Page ---
    return render(request, 'registration/home.html', {
        'user': request.user,
        'user_profile': user_profile,
        'verification_status': verification_status,
        'applied_jobs': applied_jobs,
        'registered_trainings': registered_trainings,
    })



@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user using custom Supabase backend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Get user role from session
            user_role = request.session.get('user_role', 'Resident')
            
            # Redirect based on role
            if user_role == 'Admin':
                return redirect('admin_dashboard')  # Update to admin dashboard if you have one
            else:
                return redirect('home')  # Redirect to home page
        else:
            # Login failed
            messages.error(request, 'Invalid username or password')
            return render(request, 'registration/login.html', {
                'form': {'non_field_errors': ['Invalid username or password']},
            })

    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# -----------------------------
# Admin Views
# -----------------------------
def is_admin(user):
    try:
        return user.useraccount.role in ['Admin']
    except:
        return False

@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Admins only.")
        return redirect('home')

    jobs = Job.objects.all().order_by('-date_posted')
    trainings = Training.objects.all().order_by('-date_scheduled')
    return render(request, 'admin/dashboard.html', {
        'jobs': jobs,
        'trainings': trainings
    })

@login_required
def admin_post_job(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Admins only.")
        return redirect('home')

    official = Official.objects.filter(user=request.user.useraccount).first()
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        status = request.POST.get('status')

        Job.objects.create(
            title=title,
            description=description,
            requirements=requirements,
            posted_by=official,
            status=status
        )
        messages.success(request, "✅ Job posted successfully!")
        return redirect('admin_dashboard')

    return render(request, 'admin/post_job.html')

@login_required
def admin_post_training(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Admins only.")
        return redirect('home')

    official = Official.objects.filter(user=request.user.useraccount).first()
    if request.method == 'POST':
        training_name = request.POST.get('training_name')
        description = request.POST.get('description')
        date_scheduled = request.POST.get('date_scheduled')
        location = request.POST.get('location')
        status = request.POST.get('status')

        Training.objects.create(
            training_name=training_name,
            description=description,
            date_scheduled=date_scheduled,
            location=location,
            status=status,
            organizer=official
        )
        messages.success(request, "✅ Training posted successfully!")
        return redirect('admin_dashboard')

    return render(request, 'admin/post_training.html')

# -----------------------------
# Official Views
# -----------------------------
@login_required
def official_dashboard(request):
    return render(request, 'official/dashboard.html')

@login_required
def post_job(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        status = request.POST.get('status')

        official = Official.objects.get(user=request.user.useraccount)

        Job.objects.create(
            title=title,
            description=description,
            requirements=requirements,
            posted_by=official,
            status=status
        )
        messages.success(request, "Job posted successfully!")
        return redirect('official_dashboard')

    return render(request, 'official/post_job.html')

@login_required
def post_training(request):
    if request.method == 'POST':
        training_name = request.POST.get('training_name')
        description = request.POST.get('description')
        date_scheduled = request.POST.get('date_scheduled')
        location = request.POST.get('location')
        status = request.POST.get('status')

        official = Official.objects.get(user=request.user.useraccount)

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

@login_required
def post_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_event = request.POST.get('date_event')
        location = request.POST.get('location')
        status = request.POST.get('status')

        official = Official.objects.get(user=request.user.useraccount)

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

# -----------------------------
# Profile (Supabase)
# -----------------------------
from supabase import create_client

SUPABASE_URL = "https://sfgnccdbgmewovbogibo.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# @login_required
# def profile_view(request):
#     if not request.user.is_authenticated:
#         return redirect('login')

#     res = supabase.table('resident').select('*').eq('user_id', request.user.id).single()

#     if res.error or not res.data:
#         user_profile = None
#         print("Supabase fetch error:", res.error)
#     else:
#         user_profile = res.data

#     return render(request, 'registration/profile.html', {
#         'user': request.user,
#         'user_profile': user_profile
#     })

@login_required
def profile_view(request):
    user = request.user
    user_profile = get_object_or_404(Resident, user__username=user.username)
    skills = ResidentSkill.objects.filter(resident=user_profile).select_related('skill')

    context = {
        'user_profile': user_profile,
        'skills': skills,
        'user': user,
    }
    return render(request, 'registration/profile.html', context)

@login_required
def edit_profile(request):
    user_account = get_object_or_404(UserAccount, username=request.user.username)
    
    resident = get_object_or_404(Resident, user=user_account)

    if request.method == "POST":
        form = ResidentForm(request.POST, instance=resident)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profile updated successfully!")
            return redirect('home')  # <-- redirect to home page
    else:
        form = ResidentForm(instance=resident)

    return render(request, 'registration/edit_profile.html', {'form': form})
