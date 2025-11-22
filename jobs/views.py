from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from datetime import datetime
from skillbridge.supabase_client import supabase
from .services.supabase_crud import (
    get_jobs,
    update_job,
    delete_job,
    get_job_by_id,
    create_job_application,
    get_resident_by_user_id,
    get_applied_jobs_by_resident,
)

# ========== LOGGING FOR AUDIT TRAIL ==========
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


# ========== HOME (RESIDENT) ==========
@login_required
def home(request):
    try:
        resident = get_resident_by_user_id(request.user.id)
        applied_jobs = get_applied_jobs_by_resident(resident["id"]) if resident else []
        return render(request, "home.html", {"applied_jobs": applied_jobs})

    except Exception as e:
        messages.error(request, f"Error loading applied jobs: {str(e)}")
        return render(request, "home.html", {"applied_jobs": []})


def job_success(request):
    return render(request, 'jobs/job_success.html')


# ==========================================================
# POST JOB (OFFICIAL)
# ==========================================================
@login_required
def post_job(request):
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


# ==========================================================
# LIST JOBS
# ==========================================================
@login_required
def list_jobs(request):
    try:
        jobs = get_jobs()
    except Exception as e:
        messages.error(request, f"Error loading jobs: {str(e)}")
        jobs = []
    return render(request, 'jobs/list_jobs.html', {'jobs': jobs})


# ==========================================================
# UPDATE JOB
# ==========================================================
@login_required
def update_job_view(request, job_id):

    email = request.user.email.strip().lower()
    official = supabase.table("registration_official").select("*").ilike("email", email).execute()
    official_data = official.data[0] if official.data else None

    if request.method == 'POST':
        try:
            updates = {
                "Title": request.POST.get('title'),
                "Description": request.POST.get('description'),
                "Status": request.POST.get('status'),
            }
            updates = {k: v for k, v in updates.items() if v}

            update_job(job_id, updates)
            log_action("edit", "job", job_id, request)
            messages.success(request, "Job updated successfully!")
            return redirect('official_dashboard')

        except Exception as e:
            messages.error(request, f"Error updating job: {str(e)}")

    try:
        job = get_job_by_id(job_id)
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        job = None

    return render(request, 'jobs/update_job.html', {'job': job, 'official': official_data})


# ==========================================================
# DELETE JOB
# ==========================================================
@login_required
def delete_job_view(request, job_id):
    try:
        delete_job(job_id)
        log_action("delete", "job", job_id, request)
        messages.success(request, "Job deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting job: {str(e)}")
    return redirect('official_dashboard')


# ==========================================================
# APPLY FOR JOB
# ==========================================================
@login_required
def apply_job(request, job_id):
    try:
        resident = get_resident_by_user_id(request.user.id)

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
                    "date_registered": datetime.utcnow().isoformat(),
                    "address": "",
                    "contact_number": "",
                    "birthdate": None,
                    "user_id": useraccount_id
                }).execute()

                resident = get_resident_by_user_id(request.user.id)

            else:
                messages.error(request, "User account not found!")
                return redirect('list_jobs')

        create_job_application(resident_id=resident['id'], job_id=job_id)
        return redirect('job_success')

    except Exception as e:
        messages.error(request, f"Error applying for job: {str(e)}")
        return redirect('list_jobs')

def job_detail(request, job_id):
    try:
        job = get_job_by_id(job_id)
    except Exception as e:
        raise Http404("Job not found")
    context = {'job': job}
    return render(request, 'jobs/job_detail.html', context)

