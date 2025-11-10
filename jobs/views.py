from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from skillbridge.supabase_client import supabase
from .services.supabase_crud import (
    create_job,
    get_jobs,
    update_job,
    delete_job,
    get_job_by_id,
    create_job_application,
    get_resident_by_user_id,
    get_applied_jobs_by_resident,   # add this here
)


from .services.supabase_crud import get_resident_by_user_id, get_applied_jobs_by_resident

@login_required
def home(request):
    try:
        resident = get_resident_by_user_id(request.user.id)
        applied_jobs = []

        if resident:
            applied_jobs = get_applied_jobs_by_resident(resident["id"])

        return render(request, "home.html", {"applied_jobs": applied_jobs})
    
    except Exception as e:
        messages.error(request, f"Error loading applied jobs: {str(e)}")
        return render(request, "home.html", {"applied_jobs": []})


# ================== SUCCESS PAGE ==================
def job_success(request):
    return render(request, 'jobs/job_success.html')


# ================== POST JOB (OFFICIALS) ==================
@login_required
def post_job(request):
    try:
        # ✅ Step 1: Normalize email and find official
        email = request.user.email.strip().lower()
        print("DEBUG: Logged in as →", email)

        # Try finding by email (case-insensitive)
        official = supabase.table("registration_official").select("*").ilike("email", email).execute()

        # If not found, try by user_id
        if not official.data:
            print("DEBUG: Trying backup search using user_id →", request.user.id)
            official = supabase.table("registration_official").select("*").eq("user_id", request.user.id).execute()

        # If still not found, show error
        if not official.data:
            print("ERROR: Official not found for", email)
            messages.error(request, "Official profile not found.")
            return render(request, 'official/dashboard.html', {'jobs': []})

        official_data = official.data[0]
        print("DEBUG: Official found →", official_data)

        # ✅ Step 2: Handle job posting
        if request.method == 'POST':
            data = request.POST
            title = data['title']
            description = data['description']
            status = data.get('status', 'Open')

            # Insert new job
            create_job(
                title=title,
                description=description,
                posted_by_id=str(official_data['id']),
                status=status
            )

            # ✅ Step 3: Add notification
            try:
                supabase.table('notifications').insert({
                    "type": "Job Posting",
                    "message": f"New job posted: {title[:100]}",
                    "link_url": "/jobs/list/",
                    "visible": True,
                    "created_at": datetime.now().isoformat()
                }).execute()
                print("DEBUG: Notification added successfully.")
            except Exception as e:
                print("Notification insert error:", e)

            messages.success(request, "✅ Job posted successfully!")
            return redirect('official_dashboard')

        # Render post job form
        return render(request, 'jobs/post_job.html')

    except Exception as e:
        print("EXCEPTION:", e)
        messages.error(request, f"Error posting job: {str(e)}")
        return redirect('official_dashboard')


# ================== LIST JOBS ==================
@login_required
def list_jobs(request):
    try:
        jobs = get_jobs()
    except Exception as e:
        messages.error(request, f"Error loading jobs: {str(e)}")
        jobs = []
    return render(request, 'jobs/list_jobs.html', {'jobs': jobs})


# ================== UPDATE JOB ==================
@login_required
def update_job_view(request, job_id):
    if request.method == 'POST':
        try:
            updates = {
                'Title': request.POST.get('title'),
                'Description': request.POST.get('description'),
                'Status': request.POST.get('status'),
            }
            updates = {k: v for k, v in updates.items() if v}
            update_job(job_id, updates)
            messages.success(request, "Job updated successfully!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error updating job: {str(e)}")

    try:
        job = get_job_by_id(job_id)
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        job = None

    return render(request, 'jobs/update_job.html', {'job': job})


# ================== DELETE JOB ==================
@login_required
def delete_job_view(request, job_id):
    try:
        delete_job(job_id)
        messages.success(request, "Job deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting job: {str(e)}")
    return redirect('list_jobs')


# ================== APPLY FOR JOB ==================
@login_required
def apply_job(request, job_id):
    try:
        resident = get_resident_by_user_id(request.user.id)

        # Auto-create resident if missing
        if not resident:
            useraccount = supabase.table("registration_useraccount") \
                .select("*").eq("username", request.user.username).execute()

            if useraccount.data:
                useraccount_id = useraccount.data[0]["id"]

                supabase.table("registration_resident").insert({
                    "first_name": request.user.first_name or "",
                    "last_name": request.user.last_name or "",
                    "email": request.user.email or "",
                    "employment_status": "Unemployed",
                    "verification_status": "Pending",
                    "date_registered": datetime.now().isoformat(),
                    "address": "",
                    "contact_number": "",
                    "birthdate": None,
                    "user_id": useraccount_id
                }).execute()

                resident = get_resident_by_user_id(request.user.id)
                if not resident:
                    messages.error(request, "Could not create resident profile.")
                    return redirect('list_jobs')
            else:
                messages.error(request, "User account not found!")
                return redirect('list_jobs')

        # Submit job application
        create_job_application(resident_id=resident['id'], job_id=job_id)

        return redirect('job_success')

    except Exception as e:
        messages.error(request, f"Error applying for job: {str(e)}")
        return redirect('list_jobs')
